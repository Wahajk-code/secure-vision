from collections import Counter, defaultdict
from datetime import date as date_type, datetime
from typing import Any, Dict, Iterable, Optional


class SummaryAgent:
    """Template-based daily report generator for interpreted operational summaries."""

    def __init__(self, stats_manager):
        self.stats_manager = stats_manager

    def generate_daily_summary(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        if target_date:
            day = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            day = date_type.today()

        payload = self.stats_manager.get_stats()
        events = [evt for evt in payload.get("events", []) if self._event_date(evt) == day]

        counts = Counter(evt.get("type", "UNKNOWN") for evt in events)
        severity_counts = Counter(self._detail(evt).get("severity", "UNKNOWN") for evt in events)
        hourly = defaultdict(int)
        critical_events = []

        for evt in events:
            dt = self._event_datetime(evt)
            if dt:
                hourly[dt.strftime("%H:00")] += 1
            details = self._detail(evt)
            if details.get("severity") == "CRITICAL" or evt.get("type") in {"WEAPON", "FIGHT", "ABANDONED_LUGGAGE"}:
                critical_events.append(evt)

        peak_hour = None
        if hourly:
            peak_hour = max(hourly.items(), key=lambda item: item[1])[0]

        text = self._render_text(day, events, counts, severity_counts, peak_hour, critical_events)

        return {
            "date": day.isoformat(),
            "total_events": len(events),
            "counts": dict(counts),
            "severity_counts": dict(severity_counts),
            "peak_hour": peak_hour,
            "critical_events": len(critical_events),
            "summary": text,
        }

    def _render_text(self, day, events, counts, severity_counts, peak_hour, critical_events: Iterable[Dict[str, Any]]) -> str:
        total = len(events)
        if total == 0:
            return f"Daily Security Summary - {day.isoformat()}\n\nNo security events were recorded today."

        critical_count = severity_counts.get("CRITICAL", 0)
        warning_count = severity_counts.get("WARNING", 0)
        weapon_count = counts.get("WEAPON", 0)
        fight_count = counts.get("FIGHT", 0)
        luggage_count = counts.get("ABANDONED_LUGGAGE", 0)

        risk = "LOW"
        if critical_count > 0 or weapon_count > 0:
            risk = "HIGH"
        elif warning_count > 0 or fight_count > 0 or luggage_count > 0:
            risk = "MEDIUM"

        lines = [
            f"Daily Security Summary - {day.isoformat()}",
            "",
            f"Overall risk level: {risk}.",
            f"Total recorded events: {total}. Critical alerts: {critical_count}. Warnings: {warning_count}.",
            "",
            "Event breakdown:",
            f"- Weapons: {weapon_count}",
            f"- Fights: {fight_count}",
            f"- Abandoned luggage: {luggage_count}",
        ]

        if peak_hour:
            lines.extend(["", f"Highest activity period: around {peak_hour}."])

        actions = []
        for evt in critical_events:
            details = self._detail(evt)
            action = details.get("recommended_action")
            if action and action not in actions:
                actions.append(action)

        if actions:
            lines.append("")
            lines.append("Supervisor review notes:")
            for action in actions[:5]:
                lines.append(f"- {action}")

        lines.append("")
        lines.append("Recommended end-of-day action: review critical evidence, confirm supervisor response times, and archive the incident records.")
        return "\n".join(lines)

    @staticmethod
    def _event_datetime(evt: Dict[str, Any]):
        raw = evt.get("datetime")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw))
        except ValueError:
            return None

    def _event_date(self, evt: Dict[str, Any]):
        dt = self._event_datetime(evt)
        return dt.date() if dt else None

    @staticmethod
    def _detail(evt: Dict[str, Any]) -> Dict[str, Any]:
        details = evt.get("details") or {}
        return details if isinstance(details, dict) else {}
