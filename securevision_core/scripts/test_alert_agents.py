import unittest

from agents.alert_rules import AlertRuleEngine
from agents.event_normalizer import normalize_pipeline_item
from agents.summary_agent import SummaryAgent


class FakeStatsManager:
    def get_stats(self):
        return {
            "events": [
                {
                    "datetime": "2026-04-23T14:10:00",
                    "type": "WEAPON",
                    "details": {
                        "severity": "CRITICAL",
                        "recommended_action": "Initiate lockdown and notify the response team.",
                    },
                    "stream_id": "desktop_stream",
                },
                {
                    "datetime": "2026-04-23T14:20:00",
                    "type": "FIGHT",
                    "details": {
                        "severity": "CRITICAL",
                        "recommended_action": "Dispatch security immediately.",
                    },
                    "stream_id": "desktop_stream",
                },
            ]
        }


class TestAlertAgents(unittest.TestCase):
    def setUp(self):
        self.rules = AlertRuleEngine()

    def test_confirmed_gun_is_critical_and_spoken(self):
        decision = self.rules.evaluate({
            "event_type": "WEAPON",
            "subtype": "gun",
            "frames_seen": 10,
            "confidence": 0.72,
            "person_present": True,
        })

        self.assertEqual(decision.severity, "CRITICAL")
        self.assertEqual(decision.risk_level, "HIGH")
        self.assertTrue(decision.should_speak)
        self.assertIn("lockdown", decision.recommended_action.lower())

    def test_unconfirmed_weapon_is_warning_without_speech(self):
        item = {
            "id": 7,
            "category": "Gun",
            "status": "WARNING",
            "details": "Verifying (3/10)",
        }
        event = normalize_pipeline_item(item)
        decision = self.rules.evaluate(event)

        self.assertEqual(event["frames_seen"], 3)
        self.assertEqual(decision.severity, "WARNING")
        self.assertFalse(decision.should_speak)

    def test_fight_confirmation_escalates_to_critical(self):
        decision = self.rules.evaluate({
            "event_type": "FIGHT",
            "status": "CONFIRMED",
            "timer": 20,
            "velocity": 6.5,
            "pose": 105.0,
        })

        self.assertEqual(decision.severity, "CRITICAL")
        self.assertIn("medical", decision.recommended_action.lower())

    def test_daily_summary_uses_interpreted_details(self):
        summary = SummaryAgent(FakeStatsManager()).generate_daily_summary("2026-04-23")

        self.assertEqual(summary["total_events"], 2)
        self.assertEqual(summary["counts"]["WEAPON"], 1)
        self.assertIn("Overall risk level: HIGH", summary["summary"])
        self.assertIn("Initiate lockdown", summary["summary"])


if __name__ == "__main__":
    unittest.main()
