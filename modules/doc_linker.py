import os
import json
import re
from typing import Optional, Dict, Any

# Define the path to the JSON file containing document link mappings
# Assumes the file is in the 'data' directory relative to this module's parent directory
DOC_LINKS_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'new_doc_links.json')

# Global variable to cache the loaded document links data in memory
# This avoids reloading the file on every call to get_doc_link
_doc_links_data: Optional[Dict[str, Any]] = None

def load_doc_links(filepath: str = DOC_LINKS_FILE_PATH) -> Dict[str, Any]: # Added type hints
    """
    Loads the document links JSON file from the specified path.

    Includes basic caching (currently disabled by commenting out the check)
    and handles file not found or JSON decoding errors gracefully.

    Args:
        filepath (str): The path to the JSON file. Defaults to DOC_LINKS_FILE_PATH.

    Returns:
        Dict[str, Any]: A dictionary containing the loaded link data,
                        or an empty dictionary if loading fails or the file is empty.
                        Expected structure: {"keyword_combo": {"topic": "...", "url": "..."}, ...}
    """
    global _doc_links_data
    # Caching check (currently disabled to ensure reload during on_ready)
    # if _doc_links_data is not None:
    #     print("Returning cached doc links.") # Debugging cache hit
    #     return _doc_links_data

    # Reset cache variable at the start of each load attempt (when caching is disabled)
    _doc_links_data = {} # Default to empty dict

    try:
        # Check if file exists and is not empty
        # Check if file exists and is not empty before attempting to read
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"Warning: Document links file is missing or empty at {filepath}. Linker will not find matches.")
            return {} # Return the empty dict

        # Open and read the JSON file
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f) # Load data

        # Validate that the loaded data is a dictionary
        if not isinstance(loaded_data, dict):
            print(f"Error: Document links file at {filepath} does not contain a valid JSON dictionary.")
            return {} # Return the empty dict

        # If loading and validation are successful, update the global cache and return the data
        _doc_links_data = loaded_data
        print(f"Document links loaded successfully from {filepath}. Entries: {len(_doc_links_data)}")
        return _doc_links_data
    except FileNotFoundError:
        print(f"Warning: Document links file not found at {filepath}. Linker will not find matches.")
        return {} # Return the empty dict set above
    except json.JSONDecodeError as e: # Added exception variable
        print(f"Error: Could not decode JSON from document links file at {filepath}. Error: {e}")
        return {} # Return the empty dict set above
    except Exception as e:
        print(f"Error loading document links from {filepath}: {e}")
        _doc_links_data = {}
        return {}

def get_doc_link(query: str) -> Optional[str]:
    """
    Searches the loaded document links for a match based on keywords in the query.
    Returns a formatted string with the link and topic, or None if no suitable match is found.
    """
    doc_links = load_doc_links() # Ensure links are loaded (uses cache if available)
    if not doc_links:
        print("Doc links data is empty, cannot find link.")
        return None # Return early if no links data is available

    # Extract potential keywords from the user's query (lowercase, words > 2 chars)
    query_keywords = set(word for word in re.findall(r'\b\w+\b', query.lower()) if len(word) > 2)
    if not query_keywords:
        print(f"No useful keywords extracted from query: '{query}'")
        return None # Return early if no keywords found in query

    best_match_key = None
    highest_score = 0

    # Iterate through the loaded link entries (key is the keyword combo, value is dict with topic/url)
    for key, data in doc_links.items():
        # Extract keywords from the entry's key (e.g., "algokit installation")
        entry_keywords = set(word for word in re.findall(r'\b\w+\b', key.lower()) if len(word) > 2)
        # Optionally, could also include keywords from the 'topic' field for broader matching:
        # if 'topic' in data and isinstance(data['topic'], str):
        #     entry_keywords.update(word for word in re.findall(r'\b\w+\b', data['topic'].lower()) if len(word) > 2)

        # Calculate match score based on the number of overlapping keywords
        match_score = len(query_keywords.intersection(entry_keywords))

        # Update best match if current score is higher
        if match_score > highest_score:
            highest_score = match_score
            best_match_key = key

    # Define a minimum score threshold to consider a match valid
    min_score_threshold = 1 # Requires at least one keyword overlap

    # Check if a sufficiently good match was found
    if highest_score >= min_score_threshold and best_match_key:
        match_data = doc_links[best_match_key]
        topic = match_data.get('topic', best_match_key) # Use the entry key as a fallback topic name
        url = match_data.get('url')

        # Ensure both topic and URL exist before formatting the response
        if topic and url:
            # Format the response string for Discord
            # Using angle brackets < > around the URL prevents Discord from auto-generating a large embed
            return f"Here's the documentation for **{topic}**: <{url}>"
        else:
            # Log a warning if a matched entry is missing required data
            print(f"Warning: Found match for key '{best_match_key}' but 'topic' or 'url' is missing in data file.")
            return None # Treat as no match if data is incomplete
    else:
        # No match found meeting the threshold
        return None

# Example usage block for testing the module directly
if __name__ == '__main__':
    # This block runs only when the script is executed directly (e.g., python modules/doc_linker.py)
    # It's useful for isolated testing without running the full bot.

    # Simulate loading data by manually setting the global cache variable
    _test_data = {
        "algokit installation": {"topic": "AlgoKit Installation", "url": "https://developer.algorand.org/docs/algokit/getting-started/"},
        "asa creation tutorial": {"topic": "ASA Creation Tutorial", "url": "https://developer.algorand.org/docs/tutorials/asa/"}
    }
    # Temporarily override the global cache for testing
    _doc_links_data = _test_data
    print("--- Running Test ---")
    print(f"Loaded test data: {_doc_links_data}")

    test_query_1 = "link for algokit installation"
    link_1 = get_doc_link(test_query_1)
    print(f"\nQuery: {test_query_1}\nResult: {link_1}")

    test_query_2 = "how do I create an asa"
    link_2 = get_doc_link(test_query_2)
    print(f"\nQuery: {test_query_2}\nResult: {link_2}")

    test_query_3 = "what is teal"
    link_3 = get_doc_link(test_query_3)
    print(f"\nQuery: {test_query_3}\nResult: {link_3}")

    # Test with empty data
    _doc_links_data = {}
    print("\n--- Testing with empty data ---")
    link_4 = get_doc_link(test_query_1)
    print(f"Query: {test_query_1}\nResult: {link_4}")
