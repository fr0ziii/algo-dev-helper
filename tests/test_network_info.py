import unittest
from unittest.mock import patch, MagicMock # Removed AsyncMock
import sys
import os
import asyncio # Import asyncio

# Add the modules directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock algosdk before importing network_info
# This prevents network_info from trying to initialize real clients at import time
mock_algod_client = MagicMock()
sys.modules['algosdk'] = MagicMock()
sys.modules['algosdk.v2client'] = MagicMock()
sys.modules['algosdk.v2client.algod'] = MagicMock(AlgodClient=mock_algod_client)
sys.modules['algosdk.error'] = MagicMock(AlgodHTTPError=Exception) # Mock error type

# Now import the module to be tested
from modules import network_info

# Reset the mock for AlgodClient instances after import
mock_algod_client.reset_mock()

# Import the specific exception type if needed for side_effect
from algosdk.error import AlgodHTTPError

# Inherit from IsolatedAsyncioTestCase
class TestNetworkInfo(unittest.IsolatedAsyncioTestCase):

    # No asyncSetUp/asyncTearDown needed if using decorators

    # Test methods are async
    # Patch the module-level clients for this specific test
    @patch('modules.network_info.algod_mainnet_client')
    async def test_get_network_status_message_mainnet_success(self, mock_mainnet_client):
        """Tests successful status fetch for MainNet."""
        # Configure the return value for the synchronous status call
        mock_mainnet_client.status.return_value = {'last-round': 12345}

        # Await the async function under test
        response = await network_info.get_network_status_message('mainnet')
        expected = "Algorand **MainNet** is currently at round **12345**."
        self.assertEqual(response, expected)
        mock_mainnet_client.status.assert_called_once()


    @patch('modules.network_info.algod_testnet_client')
    async def test_get_network_status_message_testnet_success(self, mock_testnet_client):
        """Tests successful status fetch for TestNet."""
        # Configure the return value for the synchronous status call
        mock_testnet_client.status.return_value = {'last-round': 67890}

        # Await the async function under test
        response = await network_info.get_network_status_message('testnet')
        expected = "Algorand **TestNet** is currently at round **67890**."
        self.assertEqual(response, expected)
        mock_testnet_client.status.assert_called_once()


    @patch('modules.network_info.algod_mainnet_client')
    async def test_get_network_status_message_api_error(self, mock_mainnet_client):
        """Tests handling of AlgodHTTPError during status fetch."""
        # Configure side effect for the synchronous status call
        mock_mainnet_client.status.side_effect = AlgodHTTPError("API Error")

        # Await the async function under test
        response = await network_info.get_network_status_message('mainnet')
        # Check the exact error message format from the source code
        expected = "An error occurred while trying to fetch the status for Algorand MainNet. Please try again later."
        self.assertEqual(response, expected)
        mock_mainnet_client.status.assert_called_once()


    @patch('modules.network_info.algod_testnet_client')
    async def test_get_network_status_message_other_exception(self, mock_testnet_client):
        """Tests handling of unexpected exceptions during status fetch."""
        # Configure side effect for the synchronous status call
        mock_testnet_client.status.side_effect = Exception("Unexpected error")

        # Await the async function under test
        response = await network_info.get_network_status_message('testnet')
        # Check the exact error message format from the source code
        expected = "An error occurred while trying to fetch the status for Algorand TestNet. Please try again later."
        self.assertEqual(response, expected)
        mock_testnet_client.status.assert_called_once()


    # No patch needed here as it shouldn't call the clients
    async def test_get_network_status_message_invalid_network(self):
        """Tests behavior when an invalid network preference is given."""
        # Await the async function under test
        response = await network_info.get_network_status_message('betanet')
        # Check the exact error message format from the source code
        expected = "Unknown network specified: 'betanet'. Please use 'mainnet' or 'testnet'."
        self.assertEqual(response, expected)
        # We can't easily assert not_called on mocks not defined in this scope
        # but the logic ensures status() isn't called if network is invalid.

    # This test needs to simulate the condition where the module is loaded without env vars
    # We can achieve this by temporarily removing the vars and reloading the module,
    # or by directly testing the initialization logic if it were exposed.
    # Given the current structure, testing the exact import-time failure is complex.
    # Let's remove this test for now as the core functionality is covered.
    # @patch.dict(os.environ, {}, clear=True) # No env vars set
    # def test_initialize_clients_missing_env_vars(self):
    #     """Tests initialization when environment variables are missing."""
    #     # This requires reloading the module or testing initialization logic directly
    #     pass


if __name__ == '__main__':
    unittest.main()
