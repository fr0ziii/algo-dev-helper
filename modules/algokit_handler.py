import os
import json
from typing import Optional, Dict, Any

# Define the path to the JSON file containing AlgoKit command details
# Assumes the file is in the 'data' directory relative to this module's parent directory
COMMANDS_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'algokit_commands.json')

# Global variable to cache the loaded AlgoKit commands data in memory
# This avoids reloading the file on every call to get_algokit_help
_algokit_commands_data: Optional[Dict[str, Any]] = None

def load_algokit_commands(filepath: str = COMMANDS_FILE_PATH) -> Dict[str, Any]: # Added type hints
    """
    Loads the AlgoKit commands JSON file from the specified path.

    Includes basic caching: if the commands data has already been loaded,
    it returns the cached dictionary instead of reading the file again.
    Handles file not found, JSON decoding errors, and other potential exceptions.

    Args:
        filepath (str): The path to the JSON file. Defaults to COMMANDS_FILE_PATH.

    Returns:
        Dict[str, Any]: A dictionary containing the loaded command data,
                        where keys are command names and values are dicts
                        with 'summary' and 'url'. Returns an empty dictionary
                        if loading fails.
    """
    global _algokit_commands_data
    # Return cached data if available
    if _algokit_commands_data is not None:
        # print("Returning cached AlgoKit commands.") # Debugging cache hit
        return _algokit_commands_data

    try:
        # Open and load the JSON file
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        # Basic validation (ensure it's a dictionary)
        if not isinstance(loaded_data, dict):
             print(f"Error: AlgoKit commands file at {filepath} does not contain a valid JSON dictionary.")
             _algokit_commands_data = {} # Ensure cache is empty on error
             return {}

        # Update the global cache
        _algokit_commands_data = loaded_data
        print(f"AlgoKit commands loaded successfully from {filepath}. Entries: {len(_algokit_commands_data)}")
        return _algokit_commands_data
    except FileNotFoundError:
        # Handle case where the file doesn't exist
        print(f"Error: AlgoKit commands file not found at {filepath}")
        _algokit_commands_data = {} # Ensure cache is empty on error
        return {}
    except json.JSONDecodeError as e:
        # Handle invalid JSON format
        print(f"Error: Could not decode JSON from {filepath}. Error: {e}")
        _algokit_commands_data = {} # Ensure cache is empty on error
        return {}
    except Exception as e:
        # Handle other potential file reading errors
        print(f"Error loading AlgoKit commands from {filepath}: {e}")
        _algokit_commands_data = {} # Ensure cache is empty on error
        return {}

def get_algokit_help(query: str) -> Optional[str]:
    """
    Searches the user's query for a known AlgoKit command name.

    If a command name from the loaded `algokit_commands.json` is found
    within the query, it retrieves the corresponding summary and documentation URL
    and returns them in a formatted string.

    Args:
        query (str): The user's query string.

    Returns:
        Optional[str]: A formatted help string for the found command,
                       or None if no known command name is detected in the query.
    """
    commands_data = load_algokit_commands() # Ensure commands are loaded
    if not commands_data:
        print("AlgoKit commands data is empty, cannot provide help.")
        return None # Return early if no command data is available

    query_lower = query.lower() # Use lowercase for case-insensitive matching

    # --- Command Matching Logic ---
    # Iterate through the known command names (keys of the loaded dictionary)
    found_command = None
    for command_name in commands_data.keys():
        # Basic matching: Check if the command name appears in the query.
        # This is simple but might have limitations (e.g., 'init' matching 'initializing').
        # A more robust approach might use regex with word boundaries (\b) or check
        # for specific patterns like "algokit [command]" or "command [command]".
        # Current check: is the command name present as a substring?
        # Added check: is command name present as a distinct word?
        # Added check: is "algokit [command]" or "command [command]" present?
        if (f"algokit {command_name}" in query_lower or
            f"command {command_name}" in query_lower or
            command_name in query_lower.split()): # Check if command is a distinct word
            found_command = command_name
            break # Stop searching once the first match is found

    # --- Response Formatting ---
    # If a known command was found in the query
    if found_command and found_command in commands_data:
        command_info = commands_data[found_command]
        # Retrieve summary and URL, providing defaults if they are missing
        summary = command_info.get('summary', 'No summary available.')
        url = command_info.get('url', 'No documentation URL available.')

        # TODO: Consider using Discord embeds for richer formatting.
        # Format the response string for Discord. Using < > around URL prevents auto-embed.
        return f"**`algokit {found_command}`**: {summary}\nDocs: <{url}>"
    else:
        # If no known command name was detected in the query
        # Note: The routing logic in bot.py might still send the query to other handlers (like Q&A)
        # if this function returns None.
        print(f"No specific AlgoKit command found in query: '{query}'")
        return None

# Example usage block for testing the module directly
if __name__ == '__main__':
    # This block runs only when the script is executed directly (e.g., python modules/algokit_handler.py)
    # It's useful for isolated testing without running the full bot.
    print("--- Running AlgoKit Handler Test ---")
    load_algokit_commands() # Ensure commands are loaded before testing get_algokit_help
    test_query = "Tell me about algokit deploy"
    help_text = get_algokit_help(test_query)
    if help_text:
        print(f"Query: {test_query}\nHelp:\n{help_text}")
    else:
        print(f"Query: {test_query}\nNo help found.")

    test_query_2 = "how to use init command"
    help_text_2 = get_algokit_help(test_query_2)
    if help_text_2:
        print(f"\nQuery: {test_query_2}\nHelp:\n{help_text_2}")
    else:
        print(f"Query: {test_query_2}\nNo help found.")

    test_query_3 = "what is bootstrap"
    help_text_3 = get_algokit_help(test_query_3)
    if help_text_3:
        print(f"\nQuery: {test_query_3}\nHelp:\n{help_text_3}")
    else:
        print(f"Query: {test_query_3}\nNo help found.")
