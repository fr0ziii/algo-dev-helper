"""
Handles requests for documentation links.

This module is responsible for:
- Loading documentation link mappings (topic, URL) from a JSON file.
- Matching user queries against keywords associated with these links.
- Returning a formatted string containing the best matching documentation link.
"""
import os
import json
import re  # Regular expressions for keyword extraction
from typing import Optional, Dict, Any

# --- Constants ---
# Define the path to the JSON file containing document link mappings.
# Constructs the path relative to this script, assuming the 'data' directory
# is one level up from the 'modules' directory.
DOC_LINKS_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'new_doc_links.json')

# --- Caching ---
# Global variable to cache the loaded document links data in memory.
# This avoids redundant file I/O by storing the data after the first load.
# Initialized to None; will hold the dictionary once loaded.
# NOTE: Caching check is currently commented out in the load function, meaning
# the file is reloaded every time load_doc_links is called (e.g., during on_ready).
_doc_links_data: Optional[Dict[str, Any]] = None

# --- Core Functions ---
def load_doc_links(filepath: str = DOC_LINKS_FILE_PATH) -> Dict[str, Any]:
    """
    Loads the document links data from a JSON file into memory.

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
    Searches the loaded document links data for the best match based on keywords in the user's query.

    It extracts keywords from the query and compares them against keywords derived
    from the keys (and potentially topics) in the loaded `new_doc_links.json` data.
    A simple scoring mechanism (keyword overlap count) is used to find the best match.

    Args:
        query (str): The user's query string.

    Returns:
        Optional[str]: A formatted string containing the topic and URL of the best match,
                       suitable for display in Discord (e.g., "Here's the documentation for **Topic**: <URL>").
                       Returns None if no suitable match is found above the minimum threshold.
    """
    doc_links = load_doc_links() # Ensure links are loaded (reloads file if cache check is disabled)
    if not doc_links:
        # If the links data couldn't be loaded or is empty, we can't find a link.
        print("Doc links data is empty, cannot find link.")
        return None

    # --- Keyword Extraction ---
    # Extract potential keywords from the user's query.
    # - Convert to lowercase for case-insensitive matching.
    # - Use regex `\b\w+\b` to find whole words.
    # - Filter out short words (<= 2 characters) as they are often less meaningful.
    # - Store keywords in a set for efficient intersection calculation.
    query_keywords = set(word for word in re.findall(r'\b\w+\b', query.lower()) if len(word) > 2)
    if not query_keywords:
        # If no suitable keywords are found in the query, matching is impossible.
        print(f"No useful keywords extracted from query: '{query}'")
        return None

    best_match_key = None
    highest_score = 0

    # --- Matching Logic ---
    # Iterate through each entry in the loaded document links dictionary.
    # The 'key' often represents the primary keywords (e.g., "algokit installation").
    # The 'data' is a dictionary containing 'topic' and 'url'.
    for key, data in doc_links.items():
        # Extract keywords from the entry's key using the same logic as for the query.
        entry_keywords = set(word for word in re.findall(r'\b\w+\b', key.lower()) if len(word) > 2)

        # --- Optional: Enhance matching by including topic keywords ---
        # Uncomment the following lines to also consider keywords from the 'topic' field
        # for potentially broader matching.
        # if 'topic' in data and isinstance(data['topic'], str):
        #     topic_keywords = set(word for word in re.findall(r'\b\w+\b', data['topic'].lower()) if len(word) > 2)
        #     entry_keywords.update(topic_keywords)
        # --- End Optional Enhancement ---

        # Calculate the match score as the number of common keywords between the query and the entry.
        match_score = len(query_keywords.intersection(entry_keywords))

        # Keep track of the entry with the highest score found so far.
        if match_score > highest_score:
            highest_score = match_score
            best_match_key = key # Store the key of the best matching entry

    # --- Thresholding and Response Formatting ---
    # Define a minimum score required to consider a match valid.
    # This prevents returning irrelevant links based on very weak keyword overlap.
    min_score_threshold = 1 # Requires at least one keyword to overlap. Adjust as needed.

    # Check if the best score found meets the minimum threshold.
    if highest_score >= min_score_threshold and best_match_key:
        # Retrieve the data (topic, url) for the best matching key.
        match_data = doc_links[best_match_key]
        # Get the topic, using the key itself as a fallback if 'topic' is missing.
        topic = match_data.get('topic', best_match_key)
        url = match_data.get('url') # Get the URL.

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

# --- Example Usage / Direct Execution ---
if __name__ == '__main__':
    # This block allows the script to be run directly for testing purposes
    # (e.g., using `python modules/doc_linker.py`).
    # It simulates loading data and tests the get_doc_link function with sample queries.

    print("--- Running Doc Linker Module Test ---")
    # --- Test Data Simulation ---
    # Instead of reading the file, we manually create a dictionary to simulate
    # the loaded data for isolated testing.
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
