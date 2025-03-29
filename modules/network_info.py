"""
Handles requests for Algorand network status information.

This module uses the `algosdk` library to connect to public Algorand nodes
(via AlgoNode) and retrieve the current consensus round number for MainNet or TestNet.
"""
import os
from algosdk.v2client import algod  # Import the Algod client from the Algorand SDK

# --- Configuration ---
# Get Algod client URLs from environment variables.
# If the environment variables are not set, it defaults to using public AlgoNode endpoints.
ALGOD_MAINNET_URL = os.getenv('ALGOD_MAINNET_URL', 'https://mainnet-api.algonode.cloud')
ALGOD_TESTNET_URL = os.getenv('ALGOD_TESTNET_URL', 'https://testnet-api.algonode.cloud')

# --- Client Initialization ---
# Initialize Algod clients globally. This allows the clients to be reused across
# multiple calls to get_network_status_message, avoiding reconnection overhead.
# The first argument to AlgodClient is the API token, which is empty ("") because
# public AlgoNode endpoints do not require authentication.
print(f"Initializing MainNet client for: {ALGOD_MAINNET_URL}")
algod_mainnet_client = algod.AlgodClient("", ALGOD_MAINNET_URL)
print(f"Initializing TestNet client for: {ALGOD_TESTNET_URL}")
algod_testnet_client = algod.AlgodClient("", ALGOD_TESTNET_URL)

# --- Core Function ---
async def get_network_status_message(network: str = 'mainnet') -> str:
    """
    Asynchronously fetches the current consensus round for the specified Algorand network.

    Args:
        network (str): The network to check ('mainnet' or 'testnet'). Defaults to 'mainnet'.

    Returns:
        str: A user-friendly message indicating the current round or an error message.
    """
    network_name = network.lower()  # Ensure network name is lowercase for comparison
    client = None                   # Variable to hold the selected Algod client
    network_display_name = ""       # User-friendly name for the network

    # --- Client Selection ---
    # Select the appropriate pre-initialized Algod client based on the requested network.
    if network_name == 'mainnet':
        client = algod_mainnet_client
        network_display_name = "MainNet"
    elif network_name == 'testnet':
        client = algod_testnet_client
        network_display_name = "TestNet"
    else:
        # If the network name is neither 'mainnet' nor 'testnet', return an error message.
        return f"Unknown network specified: '{network}'. Please use 'mainnet' or 'testnet'."

    # --- API Call and Response Handling ---
    try:
        # Make the synchronous API call to the selected Algod node to get its status.
        # Note: Although this function is async, client.status() itself might be blocking.
        # For high-concurrency bots, consider running blocking calls in an executor.
        status = client.status()

        # Check if the response is valid and contains the 'last-round' key.
        if status and 'last-round' in status:
            round_num = status['last-round']
            # Format a success message including the network name and round number.
            return f"Algorand **{network_display_name}** is currently at round **{round_num}**."
        else:
            # Handle cases where the status response might be malformed or missing expected data.
            print(f"Warning: Unexpected status response for {network_display_name}: {status}")
            return f"Could not retrieve valid status information for Algorand {network_display_name}."
    except Exception as e:
        # Catch potential exceptions during the API call (e.g., network errors, timeouts).
        print(f"Error fetching network status for {network_display_name}: {e}")
        # Return a user-friendly error message without exposing internal details.
        return f"An error occurred while trying to fetch the status for Algorand {network_display_name}. Please try again later."

# --- Example Usage / Direct Execution ---
if __name__ == '__main__':
    # This block allows the script to be run directly for testing purposes
    # (e.g., using `python modules/network_info.py`).
    # It demonstrates how to use the async get_network_status_message function.
    import asyncio # Need asyncio to run the async function

    print("--- Running Network Info Module Test ---")

    # Define an async function to run the tests
    async def test_status():
        print("Fetching MainNet status...")
        mainnet_status = await get_network_status_message('mainnet')
        print(mainnet_status)

        print("\nFetching TestNet status...")
        testnet_status = await get_network_status_message('testnet')
        print(testnet_status)

        print("\nFetching status for invalid network...")
        invalid_status = await get_network_status_message('invalidnet')
        print(invalid_status)

    # Run the async test function using asyncio.run()
    asyncio.run(test_status())
