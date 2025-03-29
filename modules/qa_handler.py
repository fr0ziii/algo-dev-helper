"""
Handles general Question & Answering based on a text knowledge base.

This module implements a simple keyword-matching approach to find relevant
information within a pre-defined text file (`llms-small.txt`) based on a user's query.
"""
import os
import re  # Regular expressions for keyword extraction and matching
from typing import Optional, List

# --- Constants ---
# Define the path to the knowledge base text file.
# Constructs the path relative to this script, assuming the 'data' directory
# is one level up from the 'modules' directory.
KB_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'llms-small.txt')

# --- Caching ---
# Global variable to cache the loaded knowledge base lines in memory.
# This avoids redundant file I/O by storing the lines after the first load.
# Initialized to None; will hold the list of lines once loaded.
_knowledge_base_lines: Optional[List[str]] = None

# --- Core Functions ---
def load_knowledge_base(filepath: str = KB_FILE_PATH) -> List[str]:
    """
    Loads the knowledge base text file into memory as a list of lines.

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
    Searches the loaded knowledge base (list of lines) for content relevant to the user's query.

    This function implements a simple keyword matching algorithm:
    1. Extracts meaningful keywords from the user's query (removes short words and common stop words).
    2. Iterates through each line in the loaded knowledge base.
    3. For each line, calculates a relevance score based on how many query keywords appear
       as whole words within that line (using regex `\b` for word boundaries).
    4. Identifies the line with the highest score.
    5. If the highest score meets a predefined minimum threshold, formats and returns that line
       as the answer. Otherwise, returns None.

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

    # --- Keyword Extraction from Query ---
    # Define a set of common English stop words to filter out from the query,
    # as they usually don't contribute much to identifying the topic.
    stop_words = set([
        "a", "an", "the", "is", "it", "in", "on", "of", "for", "to", "and", "or", "be", "was", "are",
        "what", "when", "where", "who", "why", "how", "do", "does", "did", "i", "you", "he", "she",
        "me", "my", "your", "his", "her", "with", "about", "if", "get", "can", "use", "from", "by",
        "tell", "about", "explain", "define" # Added some query-specific words
    ])
    # 1. Find all sequences of word characters (alphanumeric + underscore) using regex.
    query_words = re.findall(r'\b\w+\b', query.lower()) # Convert query to lowercase first.
    # 2. Filter the words: keep only those longer than 2 characters and not in the stop_words set.
    keywords = [word for word in query_words if len(word) > 2 and word not in stop_words]

    # If no keywords are left after filtering, we can't match anything
    if not keywords:
        print(f"No useful keywords extracted from query: '{query}'")
        return None

    print(f"Extracted keywords: {keywords}")

    # --- Matching and Scoring Lines in Knowledge Base ---
    best_match_score = 0        # Keep track of the highest score found so far
    best_match_line_index = -1  # Index of the line with the highest score

    # Iterate through each line in the loaded knowledge base
    for i, line in enumerate(kb_lines):
        line_lower = line.lower() # Convert KB line to lowercase for matching
        current_score = 0         # Score for the current line

        # Calculate the score for the current line:
        # Sum 1 for each query keyword found as a whole word in the line.
        # `re.escape` handles potential special characters in keywords.
        # `\b` ensures matching whole words (e.g., 'arc' matches 'arc' but not 'architecture').
        try:
            current_score = sum(1 for keyword in keywords if re.search(r'\b' + re.escape(keyword) + r'\b', line_lower))
        except re.error as e:
            # Handle rare cases where a keyword might cause a regex error
            print(f"Regex error processing keyword '{keyword}' in line {i}. Error: {e}")
            continue # Skip scoring this line if a keyword causes an error

        # If the current line has a higher score than the best found so far, update the best match
        if current_score > best_match_score:
            best_match_score = current_score
            best_match_line_index = i

    # --- Result Selection and Formatting ---
    # Define a minimum score threshold. A match is only considered relevant if its
    # score meets or exceeds this threshold. This helps filter out weak matches.
    # Value was tuned during testing.
    min_score_threshold = 3

    print(f"[QA DEBUG] Best match score: {best_match_score} at index {best_match_line_index} (Threshold: {min_score_threshold})")

    # Check if the best score meets the threshold and a valid line index was found.
    if best_match_score >= min_score_threshold and best_match_line_index != -1:
        # Retrieve the best matching line from the knowledge base using the stored index.
        response_text = kb_lines[best_match_line_index]

        # --- Optional: Context Enhancement ---
        # TODO: Consider returning surrounding lines (e.g., line before and after)
        #       to provide more context, instead of just the single best matching line.
        #       This would require adjusting the logic here and potentially the scoring.

        # --- Response Length Limiting ---
        # Limit the response length to avoid sending excessively long messages in Discord.
        max_length = 1000 # Define maximum characters for the response snippet.
        if len(response_text) > max_length:
            # Truncate the text and add ellipsis if it exceeds the max length.
            response_text = response_text[:max_length] + "..."

        # Format the final response string
        return f"Based on the knowledge base:\n>>> {response_text}"
    else:
        # Return None if no match met the minimum score threshold
        return None

# --- Example Usage / Direct Execution ---
if __name__ == '__main__':
    # This block allows the script to be run directly for testing purposes
    # (e.g., using `python modules/qa_handler.py`).
    # It demonstrates loading the KB and testing the get_answer_from_kb function.
    print("--- Running QA Handler Module Test ---")
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
