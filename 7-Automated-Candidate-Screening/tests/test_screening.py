import unittest
from screening import load_candidates, score_candidate, validate_candidate, load_jobs

class ScreeningTests(unittest.TestCase):
    def test_demo_data_validates(self):
        df = load_candidates()
        jobs = load_jobs()
        self.assertGreater(len(df), 0)
        self.assertEqual(len(df["application_id"]), len(set(df["application_id"])))
        for _, row in df.iterrows():
            self.assertEqual(validate_candidate(row.to_dict(), jobs), [])

    def test_score_has_explanation(self):
        row = load_candidates().iloc[0].to_dict()
        result = score_candidate(row)
        self.assertIsNotNone(result["score"])
        self.assertIn("skills", result["component_scores"])
        self.assertTrue(result["explanation"])

    def test_missing_data_routes_to_review(self):
        row = load_candidates().iloc[0].to_dict()
        row["email"] = ""
        result = score_candidate(row)
        self.assertIsNone(result["score"])
        self.assertEqual(result["recommended_stage"], "NEEDS_REVIEW")

if __name__ == "__main__":
    unittest.main()
