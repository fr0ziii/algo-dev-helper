import unittest
from unittest.mock import patch, mock_open
import json
import sys
import os

# Add the modules directory to the Python path
# This allows importing modules from the 'modules' directory as if tests/ were in the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules import algokit_handler

# REAL data from data/algokit_commands.json (as of 2025-03-30)
REAL_ALGOKIT_COMMANDS = {
  "bootstrap": {
    "keywords": ["bootstrap", "setup", "dependencies", "install"],
    "summary": "Expedited initial setup for any developer by installing and configuring dependencies and other key development environment setup activities.",
    "url": "https://developer.algorand.org/docs/get-details/algokit/cli-reference/#bootstrap"
  },
  "deploy": {
    "keywords": ["deploy", "contracts", "smart contracts"],
    "summary": "Deploy smart contracts from AlgoKit compliant repository.",
    "url": "https://developer.algorand.org/docs/get-details/algokit/cli-reference/#deploy"
  },
  "generate": {
    "keywords": ["generate", "code", "client", "applicationclient", "arc32"],
    "summary": "Generate code for an Algorand project (e.g., typed ApplicationClient from ARC-32 application.json).",
    "url": "https://developer.algorand.org/docs/get-details/algokit/cli-reference/#generate"
  },
  "init": {
    "keywords": ["init", "initialize", "project", "template", "new"],
    "summary": "Initializes a new project from a template, including prompting for template specific questions to be used in template rendering.",
    "url": "https://developer.algorand.org/docs/get-details/algokit/cli-reference/#init"
  },
  "localnet": {
    "keywords": ["localnet", "sandbox", "network", "start", "stop", "reset", "status", "logs"],
    "summary": "Manage the AlgoKit LocalNet (start, stop, reset, status, logs, explore, console).",
    "url": "https://developer.algorand.org/docs/get-details/algokit/cli-reference/#localnet"
  }
}

# Use the real data for mocking file content
MOCK_JSON_DATA = json.dumps(REAL_ALGOKIT_COMMANDS)

class TestAlgoKitHandler(unittest.TestCase):

    def setUp(self):
        """Clear the cache before each test."""
        algokit_handler._algokit_commands_data = None

    @patch("builtins.open", new_callable=mock_open, read_data=MOCK_JSON_DATA)
    @patch("json.load")
    def test_load_algokit_commands_success(self, mock_json_load, mock_file_open):
        """Tests successful loading of commands from the JSON file."""
        # Ensure cache is clear before test
        self.assertIsNone(algokit_handler._algokit_commands_data)
        # Configure the mock json.load to return our mock data
        mock_json_load.return_value = REAL_ALGOKIT_COMMANDS

        commands = algokit_handler.load_algokit_commands("dummy/path/algokit_commands.json")

        mock_file_open.assert_called_once_with("dummy/path/algokit_commands.json", 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
        # Check returned value and cache against the REAL data
        self.assertEqual(commands, REAL_ALGOKIT_COMMANDS)
        self.assertEqual(algokit_handler._algokit_commands_data, REAL_ALGOKIT_COMMANDS)


    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_algokit_commands_file_not_found(self, mock_file_open):
        """Tests handling when the commands file is not found (returns {})."""
        # Ensure cache is clear before test
        self.assertIsNone(algokit_handler._algokit_commands_data)

        # Call the function - it should catch the error and return {}
        commands = algokit_handler.load_algokit_commands("nonexistent/path.json")

        mock_file_open.assert_called_once_with("nonexistent/path.json", 'r', encoding='utf-8')
        # Check that the function returned an empty dict and cache is empty dict
        self.assertEqual(commands, {})
        self.assertEqual(algokit_handler._algokit_commands_data, {})


    @patch("builtins.open", new_callable=mock_open, read_data='{"invalid json":,}')
    @patch("json.load", side_effect=json.JSONDecodeError("Expecting value", "invalid json", 0))
    def test_load_algokit_commands_invalid_json(self, mock_json_load, mock_file_open):
        """Tests handling of invalid JSON content (returns {})."""
         # Ensure cache is clear before test
        self.assertIsNone(algokit_handler._algokit_commands_data)

        # Call the function - it should catch the error and return {}
        commands = algokit_handler.load_algokit_commands("dummy/path/invalid.json")

        mock_file_open.assert_called_once_with("dummy/path/invalid.json", 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
         # Check that the function returned an empty dict and cache is empty dict
        self.assertEqual(commands, {})
        self.assertEqual(algokit_handler._algokit_commands_data, {})


    def test_get_algokit_help_found(self):
        """Tests finding help for a known command using REAL data."""
        # Pre-populate the cache with REAL data for this test
        algokit_handler._algokit_commands_data = REAL_ALGOKIT_COMMANDS

        query = "tell me about algokit deploy"
        # Use REAL summary and URL, formatted with <>
        expected_response = "**`algokit deploy`**: Deploy smart contracts from AlgoKit compliant repository.\nDocs: <https://developer.algorand.org/docs/get-details/algokit/cli-reference/#deploy>"
        response = algokit_handler.get_algokit_help(query)
        self.assertEqual(response, expected_response)

        query_init = "how to use algokit init command"
        # Use REAL summary and URL, formatted with <>
        expected_response_init = "**`algokit init`**: Initializes a new project from a template, including prompting for template specific questions to be used in template rendering.\nDocs: <https://developer.algorand.org/docs/get-details/algokit/cli-reference/#init>"
        response_init = algokit_handler.get_algokit_help(query_init)
        self.assertEqual(response_init, expected_response_init)


    def test_get_algokit_help_not_found(self):
        """Tests when the query doesn't match a known command."""
        # Use REAL data in cache
        algokit_handler._algokit_commands_data = REAL_ALGOKIT_COMMANDS

        query = "what is algokit explore?" # 'explore' is part of 'localnet', but not a top-level command key
        response = algokit_handler.get_algokit_help(query)
        self.assertIsNone(response)

        query_compile = "how to compile?" # 'compile' is not in REAL_ALGOKIT_COMMANDS
        response_compile = algokit_handler.get_algokit_help(query_compile)
        self.assertIsNone(response_compile)


    def test_get_algokit_help_empty_query(self):
        """Tests behavior with an empty query."""
        # Use REAL data in cache
        algokit_handler._algokit_commands_data = REAL_ALGOKIT_COMMANDS
        response = algokit_handler.get_algokit_help("")
        self.assertIsNone(response)


    def test_get_algokit_help_no_cache(self):
        """Tests behavior when the cache is empty (e.g., loading failed)."""
        algokit_handler._algokit_commands_cache = {}
        query = "help with algokit compile"
        response = algokit_handler.get_algokit_help(query)
        self.assertIsNone(response) # Should return None if cache is empty


if __name__ == '__main__':
    unittest.main()
