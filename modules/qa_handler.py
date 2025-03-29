import os
import re
from typing import Optional, List

# Define the path to the knowledge base text file
# Assumes the file is in the 'data' directory relative to this module's parent directory
KB_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'llms-small.txt')

# Global variable to cache the loaded knowledge base lines in memory
# This avoids reloading the file on every call to get_answer_from_kb
_knowledge_base_lines: Optional[List[str]] = None

def load_knowledge_base(filepath: str = KB_FILE_PATH) -> List[str]: # Added type hints
    """
    Loads the knowledge base text file from the specified path into a list of lines.

    Includes basic caching: if the knowledge base has already been loaded,
    it returns the cached list instead of reading the file again.
    Handles file not found and other potential exceptions during file reading.

    Args:
        filepath (str): The path to the knowledge base text file. Defaults to KB_FILE_PATH.

    Returns:
        List[str]: A list of strings, where each string is a non-empty line
                   from the knowledge base file with leading/trailing whitespace stripped.
                   Returns an empty list if loading fails.
    """
    global _knowledge_base_lines
    # Return cached data if available
    if _knowledge_base_lines is not None:
        # print("Returning cached knowledge base.") # Debugging cache hit
        return _knowledge_base_lines

    try:
        # Open and read the file line by line
        with open(filepath, 'r', encoding='utf-8') as f:
            # Create a list of lines, stripping whitespace and skipping empty lines
            loaded_lines = [line.strip() for line in f if line.strip()]

        # Update the global cache
        _knowledge_base_lines = loaded_lines
        print(f"Knowledge base loaded successfully from {filepath}. Lines: {len(_knowledge_base_lines)}")
        return _knowledge_base_lines
    except FileNotFoundError:
        # Handle case where the file doesn't exist
        print(f"Error: Knowledge base file not found at {filepath}")
        _knowledge_base_lines = [] # Ensure cache is empty on error
        return []
    except Exception as e:
        # Handle other potential file reading errors
        print(f"Error loading knowledge base from {filepath}: {e}")
        _knowledge_base_lines = [] # Ensure cache is empty on error
        return []

def get_answer_from_kb(query: str) -> Optional[str]:
    """
    Searches the loaded knowledge base lines for content relevant to the user's query.

    Uses a simple keyword matching approach:
    1. Extracts keywords from the query (lowercase, >2 chars, not stop words).
    2. Iterates through each line of the knowledge base.
    3. Counts how many query keywords appear as whole words in the line.
    4. Returns the line with the highest keyword count, if it meets a minimum threshold.

    Args:
        query (str): The user's query string.

    Returns:
        Optional[str]: A formatted string containing the most relevant snippet found,
                       prefixed with "Based on the knowledge base:", or None if no
                       sufficiently relevant match is found.
    """
    kb_lines = load_knowledge_base() # Ensure KB is loaded (uses cache if available)
    if not kb_lines:
        print("Knowledge base is empty, cannot provide answer.")
        return None # Return early if KB is not loaded

    # --- Keyword Extraction ---
    # Define a set of common English stop words to ignore
    stop_words = set([
        "a", "an", "the", "is", "it", "in", "on", "of", "for", "to", "and", "or", "be", "was", "are",
        "what", "when", "where", "who", "why", "how", "do", "does", "did", "i", "you", "he", "she",
        "me", "my", "your", "his", "her", "with", "about", "if", "get", "can", "use", "from", "by"
    ])
    # Find all whole words in the lowercase query
    query_words = re.findall(r'\b\w+\b', query.lower())
    # Filter out short words and stop words to get meaningful keywords
    keywords = [word for word in query_words if len(word) > 2 and word not in stop_words]

    # If no keywords are left after filtering, we can't match anything
    if not keywords:
        print(f"No useful keywords extracted from query: '{query}'")
        return None

    print(f"Extracted keywords: {keywords}")

    # --- Matching and Scoring ---
    best_match_score = 0
    best_match_line_index = -1

    # Iterate through each line in the knowledge base
    for i, line in enumerate(kb_lines):
        line_lower = line.lower() # Use lowercase for case-insensitive matching
        current_score = 0
        try:
            # Count how many keywords appear as whole words in the current line
            # Using regex \b ensures we match whole words only (e.g., 'arc' doesn't match 'architecture')
            current_score = sum(1 for keyword in keywords if re.search(r'\b' + re.escape(keyword) + r'\b', line_lower))
        except re.error as e:
            # Handle potential regex errors with specific keywords (unlikely but possible)
            print(f"Regex error processing keyword: {keyword} in line {i}. Error: {e}")
            continue # Skip this keyword/line combination on regex error

        # If the current line has a higher score than the best found so far, update the best match
        if current_score > best_match_score:
            best_match_score = current_score
            best_match_line_index = i

    # --- Result Selection ---
    # Define a minimum score threshold for a match to be considered relevant
    # This was increased from 1 to 3 during testing to improve relevance and reduce false positives
    min_score_threshold = 3

    print(f"Best match score: {best_match_score} at index {best_match_line_index} (Threshold: {min_score_threshold})")

    # Check if the best score meets the threshold and a valid line index was found
    if best_match_score >= min_score_threshold and best_match_line_index != -1:
        # Retrieve the best matching line from the knowledge base
        response_text = kb_lines[best_match_line_index]

        # TODO: Consider returning surrounding lines for better context instead of just the single best line.

        # Limit response length to avoid sending excessively long messages in Discord
        max_length = 1000 # Max characters for the response snippet
        if len(response_text) > max_length:
            response_text = response_text[:max_length] + "..." # Truncate and add ellipsis

        # Format the final response string
        return f"Based on the knowledge base:\n>>> {response_text}"
    else:
        # Return None if no match met the minimum score threshold
        return None

# Example usage block for testing the module directly
if __name__ == '__main__':
    # This block runs only when the script is executed directly (e.g., python modules/qa_handler.py)
    # It's useful for isolated testing without running the full bot.
    print("--- Running QA Handler Test ---")
    load_knowledge_base() # Ensure KB is loaded before testing get_answer_from_kb
    test_query = "What is an Algorand Standard Asset?"
    answer = get_answer_from_kb(test_query)
    if answer:
        print(f"Query: {test_query}\nAnswer:\n{answer}")
    else:
        print(f"Query: {test_query}\nNo relevant answer found.")

    test_query_2 = "algokit compile"
    answer_2 = get_answer_from_kb(test_query_2)
    if answer_2:
        print(f"\nQuery: {test_query_2}\nAnswer:\n{answer_2}")
    else:
        print(f"Query: {test_query_2}\nNo relevant answer found.")
