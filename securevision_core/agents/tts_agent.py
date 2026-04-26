import queue
import platform
import subprocess
import threading
import time
from typing import Dict, Optional, Tuple

from utils.logger import setup_logger

logger = setup_logger(__name__)


class TTSAgent:
    """Non-blocking text-to-speech queue with cooldowns and optional pyttsx3."""

    def __init__(
        self,
        cooldown_seconds: float = 5.0,
        critical_cooldown_seconds: float = 8.0,
        fight_critical_cooldown_seconds: float = 10.0,
        enabled: bool = True,
    ):
        self.cooldown_seconds = cooldown_seconds
        self.critical_cooldown_seconds = critical_cooldown_seconds
        self.fight_critical_cooldown_seconds = fight_critical_cooldown_seconds
        self.enabled = enabled
        self._last_spoken: Dict[Tuple[str, str, str, str, str, str], float] = {}
        self._queue: "queue.PriorityQueue[tuple[int, float, tuple, str]]" = queue.PriorityQueue()
        self._pending_messages = set()
        self._speaking_messages = set()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._engine = None
        self._engine_failed = False

        if self.enabled:
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def enqueue_decision(self, decision) -> bool:
        if not self.enabled or not decision.should_speak:
            return False

        metadata = decision.metadata or {}
        camera_key = str(metadata.get("camera_id") or metadata.get("camera_name") or "camera")
        sector_key = str(metadata.get("sector") or "")
        area_key = str(metadata.get("area") or "")
        subtype_key = str(getattr(decision, "subtype", metadata.get("subtype") or "generic"))
        severity_key = str(decision.severity).upper()
        if str(decision.event_type).upper() == "FIGHT" and severity_key == "CRITICAL":
            key = (
                decision.event_type,
                subtype_key,
                severity_key,
                camera_key,
                "",
                "",
            )
            active_cooldown = self.fight_critical_cooldown_seconds
        else:
            key = (
                decision.event_type,
                subtype_key,
                severity_key,
                camera_key,
                sector_key,
                area_key,
            )
            active_cooldown = self.critical_cooldown_seconds if severity_key == "CRITICAL" else self.cooldown_seconds
        now = time.time()
        last = self._last_spoken.get(key, 0)
        if now - last < active_cooldown:
            logger.debug(
                "[TTS cooldown] event=%s subtype=%s severity=%s location=%s/%s/%s next_repeat_in=%.1fs",
                key[0],
                key[1],
                key[2],
                key[3],
                key[4],
                key[5],
                active_cooldown - (now - last),
            )
            return False

        message = decision.spoken_message.strip()
        with self._lock:
            if message in self._pending_messages or message in self._speaking_messages:
                logger.info("[TTS COLLAPSED] duplicate_pending speech=%s", message)
                return False
            self._pending_messages.add(message)
            self._last_spoken[key] = now

        self._queue.put((decision.priority, now, key, message))
        return True

    def _worker(self):
        while True:
            _, _, key, message = self._queue.get()
            try:
                with self._lock:
                    self._pending_messages.discard(message)
                    self._speaking_messages.add(message)
                self._speak(message)
            except Exception as exc:
                logger.error(f"[TTS] Failed to speak alert: {exc}")
            finally:
                with self._lock:
                    self._speaking_messages.discard(message)
                self._queue.task_done()

    def _speak(self, message: str):
        if self._engine_failed:
            logger.warning(f"[TTS disabled] {message}")
            return

        logger.info("[TTS START] %s", message)
        try:
            if platform.system().lower() == "windows":
                try:
                    self._speak_windows(message)
                except Exception as windows_exc:
                    logger.warning("[TTS WINDOWS FAILED] %s error=%s", message, windows_exc)
                    self._speak_pyttsx3(message)
            else:
                self._speak_pyttsx3(message)
            logger.info("[TTS DONE] %s", message)
        except Exception as exc:
            self._engine_failed = True
            logger.error("[TTS FAILED] %s error=%s", message, exc)
            raise

    def _speak_windows(self, message: str):
        escaped = message.replace("'", "''")
        command = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Rate = 3; "
            "$s.Volume = 100; "
            f"$s.Speak('{escaped}'); "
            "$s.Dispose();"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=35,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "PowerShell speech command failed")

    def _speak_pyttsx3(self, message: str):
        if self._engine is None:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 210)
        self._engine.say(message)
        self._engine.runAndWait()

    def _legacy_speak_pyttsx3(self, message: str):
        try:
            if self._engine is None:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", 210)
            self._engine.say(message)
            self._engine.runAndWait()
        except Exception:
            self._engine_failed = True
            logger.warning(f"[TTS unavailable] {message}")
