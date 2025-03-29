import os
from algosdk.v2client import algod

# Get Algod client URLs from environment variables, with defaults to public AlgoNode endpoints
ALGOD_MAINNET_URL = os.getenv('ALGOD_MAINNET_URL', 'https://mainnet-api.algonode.cloud')
ALGOD_TESTNET_URL = os.getenv('ALGOD_TESTNET_URL', 'https://testnet-api.algonode.cloud')

# Initialize Algod clients globally for reuse
# We don't need API keys (first arg) for public AlgoNode endpoints
algod_mainnet_client = algod.AlgodClient("", ALGOD_MAINNET_URL)
algod_testnet_client = algod.AlgodClient("", ALGOD_TESTNET_URL)

async def get_network_status_message(network: str = 'mainnet') -> str: # Added type hints
    """
    Fetches the current status (last round) for the specified Algorand network.

    Args:
        network (str): The network to check ('mainnet' or 'testnet'). Defaults to 'mainnet'.

    Returns:
        str: A user-friendly message indicating the current round or an error message.
    """
    network_name = network.lower() # Ensure case-insensitivity
    client = None
    network_display_name = "" # Initialize display name

    # Select the appropriate Algod client based on the requested network
    if network_name == 'mainnet':
        client = algod_mainnet_client
        network_display_name = "MainNet"
    elif network_name == 'testnet':
        client = algod_testnet_client
        network_display_name = "TestNet"
    else:
        # Handle invalid network input
        return f"Unknown network specified: '{network}'. Please use 'mainnet' or 'testnet'."

    try:
        # Make the API call to get the node status
        status = client.status()
        # Check if the response is valid and contains the last round
        if status and 'last-round' in status:
            round_num = status['last-round']
            # Format the success message
            return f"Algorand **{network_display_name}** is currently at round **{round_num}**."
        else:
            # Handle cases where the status response might be malformed or missing data
            return f"Could not retrieve status information for Algorand {network_display_name}."
    except Exception as e:
        # Catch potential exceptions during the API call (e.g., network issues, timeouts)
        print(f"Error fetching network status for {network_display_name}: {e}")
        # Return a user-friendly error message
        return f"An error occurred while trying to fetch the status for Algorand {network_display_name}. Please try again later."

if __name__ == '__main__':
    # Example usage (for testing the module directly)
    import asyncio

    async def test_status():
        mainnet_status = await get_network_status_message('mainnet')
        print(mainnet_status)
        testnet_status = await get_network_status_message('testnet')
        print(testnet_status)
        invalid_status = await get_network_status_message('invalid')
        print(invalid_status)

    asyncio.run(test_status())
