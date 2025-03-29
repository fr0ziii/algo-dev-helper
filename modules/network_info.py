import os
from algosdk.v2client import algod

# Get Algod client URLs from environment variables
ALGOD_MAINNET_URL = os.getenv('ALGOD_MAINNET_URL', 'https://mainnet-api.algonode.cloud')
ALGOD_TESTNET_URL = os.getenv('ALGOD_TESTNET_URL', 'https://testnet-api.algonode.cloud')

# Initialize Algod clients
# We don't need API keys for public AlgoNode endpoints
algod_mainnet_client = algod.AlgodClient("", ALGOD_MAINNET_URL)
algod_testnet_client = algod.AlgodClient("", ALGOD_TESTNET_URL)

async def get_network_status_message(network='mainnet'):
    """
    Fetches the current status (last round) for the specified Algorand network.

    Args:
        network (str): The network to check ('mainnet' or 'testnet'). Defaults to 'mainnet'.

    Returns:
        str: A message indicating the current round or an error message.
    """
    network_name = network.lower()
    client = None

    if network_name == 'mainnet':
        client = algod_mainnet_client
        network_display_name = "MainNet"
    elif network_name == 'testnet':
        client = algod_testnet_client
        network_display_name = "TestNet"
    else:
        return f"Unknown network specified: '{network}'. Please use 'mainnet' or 'testnet'."

    try:
        # Call the synchronous status() method
        status = client.status()
        if status and 'last-round' in status:
            round_num = status['last-round']
            return f"Algorand **{network_display_name}** is currently at round **{round_num}**."
        else:
            return f"Could not retrieve status information for Algorand {network_display_name}."
    except Exception as e:
        print(f"Error fetching network status for {network_display_name}: {e}")
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
