import unittest
from unittest.mock import patch, mock_open
import sys
import os

# Add the modules directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules import qa_handler

# Mock data representing the content of llms-small.txt
MOCK_KB_CONTENT = """
This is the first paragraph about Algorand basics. It mentions ASA and ARC standards.
This second paragraph discusses TEAL and AVM concepts. The Algorand Virtual Machine (AVM) executes TEAL code.
A third section talks about AlgoKit, specifically how to initialize a project using 'algokit init'. AlgoKit simplifies development.
Final paragraph about Pure Proof-of-Stake (PPoS).
"""

# Split into paragraphs/lines as the handler might process it
MOCK_KB_PARAGRAPHS = [p.strip() for p in MOCK_KB_CONTENT.strip().split('\n')]

class TestQaHandler(unittest.TestCase):

    def setUp(self):
        """Reset cache and threshold before each test."""
        qa_handler._knowledge_base_lines = None # Reset cache to None
        # Set the threshold used in tests, matching the value from progress.md
        qa_handler.min_score_threshold = 3

    @patch("builtins.open", new_callable=mock_open, read_data=MOCK_KB_CONTENT)
    def test_load_knowledge_base_success(self, mock_file_open):
        """Tests successful loading of the knowledge base file."""
        # Ensure cache is clear
        self.assertIsNone(qa_handler._knowledge_base_lines)

        kb = qa_handler.load_knowledge_base("dummy/path/llms-small.txt")

        mock_file_open.assert_called_once_with("dummy/path/llms-small.txt", 'r', encoding='utf-8')
        # Check if the loaded content is split into paragraphs/lines correctly
        self.assertEqual(kb, MOCK_KB_PARAGRAPHS)
        # Ensure the internal cache is updated
        self.assertEqual(qa_handler._knowledge_base_lines, MOCK_KB_PARAGRAPHS)


    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_knowledge_base_file_not_found(self, mock_file_open):
        """Tests handling when the knowledge base file is not found (returns [])."""
         # Ensure cache is clear
        self.assertIsNone(qa_handler._knowledge_base_lines)

        # Function should catch error and return []
        kb = qa_handler.load_knowledge_base("nonexistent/path.txt")

        mock_file_open.assert_called_once_with("nonexistent/path.txt", 'r', encoding='utf-8')
        # Check returned value and cache are []
        self.assertEqual(kb, [])
        self.assertEqual(qa_handler._knowledge_base_lines, [])


    def test_get_answer_from_kb_found_good_match(self):
        """Tests finding an answer with a high keyword match score using MOCK data."""
        # Pre-populate the cache with MOCK data
        qa_handler._knowledge_base_lines = MOCK_KB_PARAGRAPHS

        query = "Tell me about AVM and TEAL concepts" # Keywords: avm, teal, concepts (score 3 on para 2)
        # Expecting the second paragraph, formatted correctly
        expected_response = "Based on the knowledge base:\n>>> This second paragraph discusses TEAL and AVM concepts. The Algorand Virtual Machine (AVM) executes TEAL code."
        response = qa_handler.get_answer_from_kb(query)
        self.assertEqual(response, expected_response)


    def test_get_answer_from_kb_found_case_insensitive(self):
        """Tests case-insensitivity of keyword matching using MOCK data."""
        # Pre-populate the cache with MOCK data
        qa_handler._knowledge_base_lines = MOCK_KB_PARAGRAPHS
        query = "what is pure proof-of-stake (ppos)?" # Keywords: pure, proof, stake, ppos (score 4 on para 4)
        # Expecting the last paragraph, formatted correctly
        expected_response = "Based on the knowledge base:\n>>> Final paragraph about Pure Proof-of-Stake (PPoS)."
        response = qa_handler.get_answer_from_kb(query)
        self.assertEqual(response, expected_response)


    def test_get_answer_from_kb_partial_match_below_threshold(self):
        """Tests when keyword matches are below the score threshold using MOCK data."""
        # Pre-populate the cache with MOCK data
        qa_handler._knowledge_base_lines = MOCK_KB_PARAGRAPHS
        qa_handler.min_score_threshold = 3 # Explicitly set for clarity

        query = "algorand standards" # Keywords: algorand, standards (score 2 on para 1)
        response = qa_handler.get_answer_from_kb(query)
        self.assertIsNone(response)


    def test_get_answer_from_kb_no_match(self):
        """Tests when the query keywords don't match anything in MOCK data."""
        # Pre-populate the cache with MOCK data
        qa_handler._knowledge_base_lines = MOCK_KB_PARAGRAPHS
        query = "information about blockchain explorers" # Keywords: information, blockchain, explorers (score 0)
        response = qa_handler.get_answer_from_kb(query)
        self.assertIsNone(response)


    def test_get_answer_from_kb_empty_query(self):
        """Tests behavior with an empty query."""
        qa_handler._knowledge_base_cache = MOCK_KB_PARAGRAPHS
        response = qa_handler.get_answer_from_kb("")
        self.assertIsNone(response)


    def test_get_answer_from_kb_no_cache(self):
        """Tests behavior when the cache is empty."""
        qa_handler._knowledge_base_cache = []
        query = "what is TEAL?"
        response = qa_handler.get_answer_from_kb(query)
        self.assertIsNone(response)


if __name__ == '__main__':
    unittest.main()
