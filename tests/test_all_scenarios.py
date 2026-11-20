import sys
from pathlib import Path

# Add project root to sys.path so 'src' can be imported anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import unittest
import pandas as pd
from src.config import JSON_FILE, CSV_FILE, SENDER_EMAIL
from src.database import load_file_seminars, get_seminars
from src.parser import parse_dates_and_location
from src.agent import chat_with_agent, reset_session, session_state
from src.ui import submit_final_form, populate_form_from_selection, build_demo


class TestSeminarAgentAllScenarios(unittest.TestCase):
    """
    Exhaustive Test Suite covering both Positive and Negative/Edge-Case scenarios
    to guarantee ZERO errors across the entire application.
    """

    def setUp(self):
        """Reset session state before every test to ensure 100% isolation."""
        reset_session()

    # ==========================================================================
    # POSITIVE TEST CASES
    # ==========================================================================
    def test_pos_01_database_loading(self):
        """Verifies database file exists and contains 100+ valid records."""
        self.assertTrue(JSON_FILE.exists(), "data/seminars_data.json must exist")
        df = load_file_seminars()
        self.assertGreaterEqual(len(df), 100, "Database must contain at least 100 seminars")
        required_cols = ["id", "title", "country", "state", "city", "university", "type", "date", "status"]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

    def test_pos_02_parser_month_and_location_variants(self):
        """Verifies parser recognizes various date formats, month names, and aliases."""
        # Exact dates
        d1, d2, loc, is_for = parse_dates_and_location("2026-03-05 to 2026-03-25 in Pune")
        self.assertEqual(d1, "2026-03-05")
        self.assertEqual(d2, "2026-03-25")
        self.assertEqual(loc, "pune")
        self.assertFalse(is_for)

        # Single month
        d1, d2, loc, is_for = parse_dates_and_location("In July in Gujarat")
        self.assertEqual(d1, "2026-07-01")
        self.assertEqual(d2, "2026-07-31")
        self.assertEqual(loc, "gujarat")
        self.assertFalse(is_for)

        # Month range
        d1, d2, loc, is_for = parse_dates_and_location("From April to June in Maharashtra")
        self.assertEqual(d1, "2026-04-01")
        self.assertEqual(d2, "2026-06-30")
        self.assertEqual(loc, "maharashtra")
        self.assertFalse(is_for)

        # City aliases
        _, _, loc, _ = parse_dates_and_location("Seminars in Bengaluru")
        self.assertEqual(loc, "bangalore")

        _, _, loc, _ = parse_dates_and_location("Seminars in MP")
        self.assertEqual(loc, "madhya pradesh")

    def test_pos_03_seminar_filtering(self):
        """Verifies date and location filtering produces correct records."""
        df = get_seminars("2026-03-01", "2026-03-31", "maharashtra", use_ai=False)
        self.assertFalse(df.empty, "Should find seminars in Maharashtra in March")
        self.assertTrue(all(df["date"].str.startswith("2026-03")))

    def test_pos_04_full_conversational_registration_flow(self):
        """Verifies complete 4-step conversation flow from search to confirmation."""
        # Step 1: Search
        r1 = asyncio.run(chat_with_agent("In March in Maharashtra", []))
        self.assertIn("1.", r1)
        self.assertEqual(session_state["step"], "SHOW_OPTIONS")

        # Step 2: Option selection
        r2 = asyncio.run(chat_with_agent("1", []))
        self.assertIn("You selected", r2)
        self.assertEqual(session_state["step"], "ASK_DETAILS")

        # Step 3: Enter Details
        r3 = asyncio.run(chat_with_agent("Dilip Kirar, enggdilipkirar@gmail.com", []))
        self.assertIn("Please Verify Your Registration Details", r3)
        self.assertIn("Dilip Kirar", r3)
        self.assertIn("enggdilipkirar@gmail.com", r3)
        self.assertEqual(session_state["step"], "VERIFY")

        # Step 4: Confirm
        r4 = asyncio.run(chat_with_agent("Confirm", []))
        self.assertIn("REGISTRATION CONFIRMED", r4)
        self.assertEqual(session_state["step"], "CONFIRMED")

    def test_pos_05_manual_form_submission(self):
        """Verifies Tab 2 manual form submission works for valid seminar."""
        df = load_file_seminars()
        open_sem = df[df["status"] == "Open"].iloc[0]
        res = submit_final_form("Dilip Kirar", "enggdilipkirar@gmail.com", open_sem["id"], open_sem["date"])
        self.assertIn("REGISTRATION CONFIRMED", res)

    def test_pos_06_form_auto_populate_helper(self):
        """Verifies dropdown selection returns ID and date."""
        df = load_file_seminars()
        sem_id = df.iloc[0]["id"]
        ret_id, ret_date = populate_form_from_selection(sem_id)
        self.assertEqual(ret_id, sem_id)
        self.assertEqual(ret_date, df.iloc[0]["date"])

    def test_pos_07_session_reset(self):
        """Verifies user can reset session at any point."""
        asyncio.run(chat_with_agent("In March in Gujarat", []))
        self.assertEqual(session_state["step"], "SHOW_OPTIONS")

        res = asyncio.run(chat_with_agent("restart", []))
        self.assertIn("Search Reset", res)
        self.assertEqual(session_state["step"], "ASK_SEARCH")

    # ==========================================================================
    # NEGATIVE / EDGE-CASE TEST CASES
    # ==========================================================================
    def test_neg_01_out_of_range_dates(self):
        """Verifies query with past/future dates with no events returns helpful suggestions."""
        res = asyncio.run(chat_with_agent("From 2020-01-01 to 2020-01-15 in Gujarat", []))
        self.assertIn("No seminars found", res)
        self.assertIn("We have 100+ seminars", res)

    def test_neg_02_unknown_location(self):
        """Verifies non-existent / foreign location returns helpful notice without crash."""
        res = asyncio.run(chat_with_agent("In Tokyo in December", []))
        self.assertTrue("No seminars found" in res or "India-Only" in res)

    def test_neg_03_empty_or_whitespace_input(self):
        """Verifies empty or whitespace queries don't crash."""
        res = asyncio.run(chat_with_agent("   ", []))
        self.assertIn("Welcome", res)

    def test_neg_04_injection_strings(self):
        """Verifies special symbols or injection attempts are safely treated as text."""
        res = asyncio.run(chat_with_agent("'; DROP TABLE seminars; -- in Pune", []))
        self.assertTrue(len(res) > 0)
        self.assertNotEqual(session_state["step"], "ERROR")

    def test_neg_05_invalid_option_index(self):
        """Verifies selecting an out-of-bounds option index shows warning."""
        asyncio.run(chat_with_agent("In March in Maharashtra", []))
        self.assertEqual(session_state["step"], "SHOW_OPTIONS")

        # User types invalid option number 99
        res = asyncio.run(chat_with_agent("99", []))
        self.assertIn("Invalid option", res)
        self.assertEqual(session_state["step"], "SHOW_OPTIONS")

    def test_neg_06_non_numeric_option(self):
        """Verifies selecting non-numeric text in options step shows warning."""
        asyncio.run(chat_with_agent("In March in Maharashtra", []))
        self.assertEqual(session_state["step"], "SHOW_OPTIONS")

        res = asyncio.run(chat_with_agent("xyz", []))
        self.assertIn("Invalid option", res)
        self.assertEqual(session_state["step"], "SHOW_OPTIONS")

    def test_neg_07_selecting_closed_seminar(self):
        """Verifies selecting a CLOSED seminar blocks registration."""
        df = load_file_seminars()
        closed_rows = df[df["status"] == "Closed"]
        self.assertFalse(closed_rows.empty, "Database should have closed seminars for testing")
        closed_sem = closed_rows.iloc[0]

        # Set matching to test selection of closed seminar
        session_state["matching_seminars"] = [closed_sem.to_dict()]
        session_state["step"] = "SHOW_OPTIONS"

        res = asyncio.run(chat_with_agent("1", []))
        self.assertIn("CLOSED", res)
        self.assertEqual(session_state["step"], "SHOW_OPTIONS")  # Must stay on options

    def test_neg_08_rejection_during_verification(self):
        """Verifies typing non-confirm during verification asks to confirm or cancel."""
        asyncio.run(chat_with_agent("In March in Maharashtra", []))
        asyncio.run(chat_with_agent("1", []))
        asyncio.run(chat_with_agent("Dilip Kirar, enggdilipkirar@gmail.com", []))
        self.assertEqual(session_state["step"], "VERIFY")

        res = asyncio.run(chat_with_agent("Wait not yet", []))
        self.assertIn("Please reply **'Confirm'**", res)
        self.assertEqual(session_state["step"], "VERIFY")

    def test_neg_09_form_missing_name(self):
        """Verifies Tab 2 form rejects empty name."""
        res = submit_final_form("", "enggdilipkirar@gmail.com", "SEM-101", "2026-03-01")
        self.assertIn("Please enter your Full Name", res)

    def test_neg_10_form_invalid_email(self):
        """Verifies Tab 2 form rejects invalid email."""
        res = submit_final_form("Dilip Kirar", "not-an-email", "SEM-101", "2026-03-01")
        self.assertIn("Please enter a valid Email", res)

    def test_neg_11_form_invalid_seminar_id(self):
        """Verifies Tab 2 form rejects non-existent seminar ID."""
        res = submit_final_form("Dilip Kirar", "enggdilipkirar@gmail.com", "SEM-9999", "2026-03-01")
        self.assertIn("not found in database", res)

    def test_neg_12_form_closed_seminar(self):
        """Verifies Tab 2 form rejects closed seminar."""
        df = load_file_seminars()
        closed_rows = df[df["status"] == "Closed"]
        if not closed_rows.empty:
            closed_id = closed_rows.iloc[0]["id"]
            res = submit_final_form("Dilip Kirar", "enggdilipkirar@gmail.com", closed_id, "2026-03-01")
            self.assertIn("is Closed", res)


if __name__ == "__main__":
    unittest.main()
