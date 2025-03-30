import unittest
from unittest.mock import patch, mock_open
import json
import sys
import os

# Add the modules directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules import doc_linker

# REAL data from data/new_doc_links.json (as of 2025-03-30)
REAL_DOC_LINKS = {
    "algokit install guide": {
      "topic": "AlgoKit Installation",
      "url": "https://developer.algorand.org/docs/get-started/algokit/"
    },
    "create asa tutorial": {
      "topic": "ASA Creation Tutorial",
      "url": "https://developer.algorand.org/tutorials/create-and-configure-asset-using-sdk/"
    },
    "python sdk connect algod": {
      "topic": "Connecting to Algod (Python SDK)",
      "url": "https://developer.algorand.org/docs/sdks/python/"
    },
    "avm opcodes list": {
      "topic": "AVM Opcodes Reference",
      "url": "https://developer.algorand.org/docs/get_details/dapps/avm/teal/opcodes/"
    },
    "teal language spec": {
      "topic": "TEAL Language Specification",
      "url": "https://developer.algorand.org/docs/get_details/dapps/avm/teal/specification/"
    },
    "smart contract develop guide": {
      "topic": "Smart Contract Development",
      "url": "https://developer.algorand.org/docs/get_details/dapps/smart-contracts/"
    },
    "algokit project init": {
      "topic": "Project Initialization with AlgoKit",
      "url": "https://developer.algorand.org/docs/get-started/algokit/#initialize-a-new-project"
    },
    "algokit localnet setup": {
      "topic": "LocalNet Setup with AlgoKit",
      "url": "https://developer.algorand.org/docs/get-started/algokit/#localnet"
    },
    "transactions fees algorand": {
      "topic": "Transactions and Fees",
      "url": "https://developer.algorand.org/docs/get_details/transactions/"
    },
    "consensus mechanism algorand": {
      "topic": "Algorand Consensus Mechanism",
      "url": "https://developer.algorand.org/docs/get_details/algorand_consensus/"
    },
    "cryptographic sortition algorand": {
      "topic": "Cryptographic Sortition in Algorand",
      "url": "https://developer.algorand.org/docs/get_details/algorand_consensus/#cryptographic-sortition"
    },
    "state proofs algorand": {
      "topic": "State Proofs",
      "url": "https://developer.algorand.org/docs/get_details/stateproofs/"
    },
    "atomic transfers tutorial": {
      "topic": "Atomic Transfers",
      "url": "https://developer.algorand.org/docs/get_details/atomic_transfers/"
    },
    "rekey accounts guide": {
      "topic": "Rekeying Accounts",
      "url": "https://developer.algorand.org/docs/get_details/accounts/#rekeying"
    },
    "governance participation algorand": {
      "topic": "Algorand Governance",
      "url": "https://developer.algorand.org/docs/get_details/governance/"
    },
    "rest api reference": {
      "topic": "REST API Reference",
      "url": "https://developer.algorand.org/docs/rest-apis/algod/v2/"
    },
    "pure proof stake algorand": {
      "topic": "Pure Proof-of-Stake in Algorand",
      "url": "https://developer.algorand.org/docs/get_details/algorand_consensus/#pure-proof-of-stake"
    },
    "account model algorand": {
      "topic": "Algorand Account Model",
      "url": "https://developer.algorand.org/docs/get_details/accounts/"
    },
    "goal cli commands": {
      "topic": "Goal CLI Reference",
      "url": "https://developer.algorand.org/docs/clis/goal/"
    },
    "node setup config": {
      "topic": "Node Setup and Configuration",
      "url": "https://developer.algorand.org/docs/run-a-node/setup/install/"
    }
}

# Use the real data for mocking file content
MOCK_JSON_DATA = json.dumps(REAL_DOC_LINKS)

class TestDocLinker(unittest.TestCase):

    def setUp(self):
        """Clear the cache before each test."""
        # Although caching is disabled in the module, clearing it ensures clean state
        doc_linker._doc_links_data = None

    # Patch functions within the module's scope
    @patch("modules.doc_linker.os.path.exists", return_value=True)
    @patch("modules.doc_linker.os.path.getsize", return_value=100) # Mock non-empty file size
    @patch("modules.doc_linker.open", new_callable=mock_open, read_data=MOCK_JSON_DATA)
    @patch("modules.doc_linker.json.load")
    def test_load_doc_links_success(self, mock_json_load, mock_file_open, mock_getsize, mock_exists):
        """Tests successful loading of doc links from the JSON file."""
        # Ensure cache is clear
        self.assertIsNone(doc_linker._doc_links_data)
        mock_json_load.return_value = REAL_DOC_LINKS

        links = doc_linker.load_doc_links("dummy/path/new_doc_links.json")

        mock_file_open.assert_called_once_with("dummy/path/new_doc_links.json", 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
        # Check returned value and cache against REAL data
        self.assertEqual(links, REAL_DOC_LINKS)
        self.assertEqual(doc_linker._doc_links_data, REAL_DOC_LINKS)


    @patch("modules.doc_linker.os.path.exists", return_value=False) # Mock file not existing
    def test_load_doc_links_file_not_found(self, mock_exists):
        """Tests handling when the links file is not found (returns {})."""
        # Ensure cache is clear
        self.assertIsNone(doc_linker._doc_links_data)

        # Function should return {} because os.path.exists is False
        links = doc_linker.load_doc_links("nonexistent/path.json")

        mock_exists.assert_called_once_with("nonexistent/path.json")
        # Check returned value and cache are {}
        self.assertEqual(links, {})
        self.assertEqual(doc_linker._doc_links_data, {})


    @patch("modules.doc_linker.os.path.exists", return_value=True)
    @patch("modules.doc_linker.os.path.getsize", return_value=100) # Mock non-empty file size
    @patch("modules.doc_linker.open", new_callable=mock_open, read_data='{"invalid json":,}')
    @patch("modules.doc_linker.json.load", side_effect=json.JSONDecodeError("Expecting value", "invalid json", 0))
    def test_load_doc_links_invalid_json(self, mock_json_load, mock_file_open, mock_getsize, mock_exists):
        """Tests handling of invalid JSON content (returns {})."""
        # Ensure cache is clear
        self.assertIsNone(doc_linker._doc_links_data)

        # Function should catch error and return {}
        links = doc_linker.load_doc_links("dummy/path/invalid.json")

        mock_exists.assert_called_once_with("dummy/path/invalid.json")
        mock_getsize.assert_called_once_with("dummy/path/invalid.json")
        mock_file_open.assert_called_once_with("dummy/path/invalid.json", 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
        # Check returned value and cache are {}
        self.assertEqual(links, {})
        self.assertEqual(doc_linker._doc_links_data, {})


    def test_get_doc_link_found_by_keyword(self):
        """Tests finding a link using keywords based on REAL data."""
        # Pre-populate cache with REAL data
        doc_linker._doc_links_data = REAL_DOC_LINKS

        # Test case 1: AlgoKit Installation
        query = "docs for algokit setup guide" # Matches keywords in "algokit install guide"
        expected = "Here's the documentation for **AlgoKit Installation**: <https://developer.algorand.org/docs/get-started/algokit/>"
        response = doc_linker.get_doc_link(query)
        self.assertEqual(response, expected)

        # Test case 2: ASA Creation
        query = "how to create asa tutorial" # Matches keywords in "create asa tutorial"
        expected_asa = "Here's the documentation for **ASA Creation Tutorial**: <https://developer.algorand.org/tutorials/create-and-configure-asset-using-sdk/>"
        response_asa = doc_linker.get_doc_link(query)
        self.assertEqual(response_asa, expected_asa)

        # Test case 3: AVM Opcodes
        query = "where is the avm opcodes list?" # Matches keywords in "avm opcodes list"
        expected_avm = "Here's the documentation for **AVM Opcodes Reference**: <https://developer.algorand.org/docs/get_details/dapps/avm/teal/opcodes/>"
        response_avm = doc_linker.get_doc_link(query)
        self.assertEqual(response_avm, expected_avm)


    def test_get_doc_link_not_found(self):
        """Tests when the query doesn't match any keys or keywords."""
        # Pre-populate cache with REAL data
        doc_linker._doc_links_data = REAL_DOC_LINKS
        query = "documentation for pyteal" # PyTeal isn't explicitly in the keys
        response = doc_linker.get_doc_link(query)
        self.assertIsNone(response)

    def test_get_doc_link_empty_query(self):
        """Tests behavior with an empty query."""
         # Pre-populate cache with REAL data
        doc_linker._doc_links_data = REAL_DOC_LINKS
        response = doc_linker.get_doc_link("")
        self.assertIsNone(response)

    @patch('modules.doc_linker.load_doc_links', return_value={})
    def test_get_doc_link_no_cache(self, mock_load_links):
        """Tests behavior when load_doc_links returns empty (simulating no cache/load failure)."""
        # No need to set cache directly, the patch handles it.
        query = "link for asa create"
        response = doc_linker.get_doc_link(query)
        # Expect None because the mocked load_doc_links returned {}
        self.assertIsNone(response)
        mock_load_links.assert_called_once() # Ensure load_doc_links was called


if __name__ == '__main__':
    unittest.main()
