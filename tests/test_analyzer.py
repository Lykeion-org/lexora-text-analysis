import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from en_service.en_analyzer import analyze_text  # noqa: E402
from main import process_job  # noqa: E402


class AnalyzeTextTest(unittest.TestCase):
    def setUp(self):
        self.result = analyze_text("The quick girl drinks two coffees slowly.")

    def texts(self, bucket):
        return {item["text"] for item in self.result[bucket]}

    def test_sorts_words_by_part_of_speech(self):
        self.assertEqual(self.texts("objects"), {"girl", "coffees"})
        self.assertEqual(self.texts("actions"), {"drinks"})
        self.assertEqual(self.texts("modifiers"), {"quick", "slowly"})

    def test_skips_determiners_numbers_and_punctuation(self):
        everything = self.texts("objects") | self.texts("actions") | self.texts("modifiers")
        self.assertFalse(everything & {"The", "two", "."})

    def test_lemma_and_attributes(self):
        coffees = next(i for i in self.result["objects"] if i["text"] == "coffees")
        self.assertEqual(coffees["lemma"], "coffee")
        self.assertEqual(coffees["pos"], "NOUN")
        self.assertEqual(coffees["attributes"]["number"], 2)

    def test_lowercases_sentence_start_but_not_names(self):
        result = analyze_text("Bicycles rust in Amsterdam.")
        texts = {item["text"] for item in result["objects"]}
        self.assertIn("bicycles", texts)
        self.assertIn("Amsterdam", texts)

    def test_process_job_echoes_ids(self):
        out = process_job(b'{"job_id": "j1", "requester_id": "u1", "text": "Cats sleep."}')
        self.assertEqual(out["job_id"], "j1")
        self.assertEqual(out["requester_id"], "u1")
        self.assertEqual(out["original_text"], "Cats sleep.")
        self.assertIn("analysis", out)


if __name__ == "__main__":
    unittest.main()
