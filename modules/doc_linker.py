import os
import json
import re
from typing import Optional, Dict, Any

# Path to the document links JSON file
DOC_LINKS_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'new_doc_links.json')

# Global variable to cache the loaded doc links
_doc_links_data: Optional[Dict[str, Any]] = None

def load_doc_links(filepath: str = DOC_LINKS_FILE_PATH) -> Dict[str, Any]:
    """
    Loads the document links JSON file.
    Includes basic caching and handles file/JSON errors gracefully.
    Returns an empty dictionary if loading fails or file is empty.
    Expected structure: {"keyword_combo": {"topic": "...", "url": "..."}, ...}
    """
    global _doc_links_data
    # Removed caching check to force reload on each call (primarily during on_ready)
    # if _doc_links_data is not None:
    #     return _doc_links_data

    # Reset cache variable at the start of the load attempt
    _doc_links_data = {} # Default to empty

    try:
        # Check if file exists and is not empty
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"Warning: Document links file is missing or empty at {filepath}. Linker will not find matches.")
            return {} # Return the empty dict set above

        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f) # Load into temp variable

        if not isinstance(loaded_data, dict):
            print(f"Error: Document links file at {filepath} does not contain a valid JSON dictionary.")
            return {} # Return the empty dict set above

        # If successful, update the cache and return the data
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
    Returns a formatted string with the link and topic, or None if no match.
    """
    doc_links = load_doc_links()
    if not doc_links:
        return None # No links loaded

    # Simple keyword extraction from query
    query_keywords = set(word for word in re.findall(r'\b\w+\b', query.lower()) if len(word) > 2)
    if not query_keywords:
        return None

    best_match_key = None
    highest_score = 0

    # Iterate through the link entries (using the keyword_combo as the key)
    for key, data in doc_links.items():
        # Treat the key itself as potential keywords
        entry_keywords = set(word for word in re.findall(r'\b\w+\b', key.lower()) if len(word) > 2)
        # Optionally, could add keywords from the 'topic' field as well
        # if 'topic' in data and isinstance(data['topic'], str):
        #     entry_keywords.update(word for word in re.findall(r'\b\w+\b', data['topic'].lower()) if len(word) > 2)

        match_score = len(query_keywords.intersection(entry_keywords))

        if match_score > highest_score:
            highest_score = match_score
            best_match_key = key

    # Define a minimum score threshold (e.g., at least one keyword match)
    min_score_threshold = 1

    if highest_score >= min_score_threshold and best_match_key:
        match_data = doc_links[best_match_key]
        topic = match_data.get('topic', best_match_key) # Use key as fallback topic
        url = match_data.get('url')

        if topic and url:
            return f"Here's the documentation for **{topic}**: <{url}>" # Use angle brackets for Discord auto-embed suppression if desired
        else:
            print(f"Warning: Found match for key '{best_match_key}' but 'topic' or 'url' is missing.")
            return None
    else:
        return None # No sufficiently relevant match found

# Example usage (for testing)
if __name__ == '__main__':
    # Simulate populating the file for testing
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
