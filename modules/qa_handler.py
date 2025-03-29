import os
import re
from typing import Optional, List

# Path to the knowledge base file
KB_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'llms-small.txt')

# Global variable to cache the knowledge base content
_knowledge_base_lines: Optional[List[str]] = None

def load_knowledge_base(filepath: str = KB_FILE_PATH) -> List[str]:
    """
    Loads the knowledge base text file into a list of lines.
    Includes basic caching.
    """
    global _knowledge_base_lines
    if _knowledge_base_lines is not None:
        return _knowledge_base_lines

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read lines and strip leading/trailing whitespace
            _knowledge_base_lines = [line.strip() for line in f if line.strip()]
        print(f"Knowledge base loaded successfully from {filepath}. Lines: {len(_knowledge_base_lines)}")
        return _knowledge_base_lines
    except FileNotFoundError:
        print(f"Error: Knowledge base file not found at {filepath}")
        _knowledge_base_lines = [] # Set to empty list on error
        return []
    except Exception as e:
        print(f"Error loading knowledge base from {filepath}: {e}")
        _knowledge_base_lines = [] # Set to empty list on error
        return []

def get_answer_from_kb(query: str) -> Optional[str]:
    """
    Searches the knowledge base for lines/paragraphs relevant to the query
    using simple keyword matching. Returns the most relevant snippet found,
    or None if no good match is found.
    """
    kb_lines = load_knowledge_base()
    if not kb_lines:
        return None # No knowledge base loaded

    # Improved keyword extraction: lowercase, ignore short words, remove common stop words
    stop_words = set([
        "a", "an", "the", "is", "it", "in", "on", "of", "for", "to", "and", "or",
        "what", "when", "where", "who", "why", "how", "do", "does", "i", "you",
        "me", "my", "your", "with", "about", "if", "get", "can", "use"
    ])
    query_words = re.findall(r'\b\w+\b', query.lower())
    keywords = [word for word in query_words if len(word) > 2 and word not in stop_words]

    if not keywords:
        print(f"No useful keywords extracted from query: '{query}'")
        return None # No useful keywords in query

    print(f"Extracted keywords: {keywords}")

    best_match_score = 0
    best_match_line_index = -1

    # Iterate through lines to find the best match based on whole word keyword count
    for i, line in enumerate(kb_lines):
        line_lower = line.lower()
        current_score = 0
        try:
            # Use regex for whole word matching
            current_score = sum(1 for keyword in keywords if re.search(r'\b' + re.escape(keyword) + r'\b', line_lower))
        except re.error as e:
            print(f"Regex error processing keyword: {keyword} in line {i}. Error: {e}")
            continue # Skip this keyword/line combination on regex error

        # Basic scoring: prioritize lines with more keyword matches
        if current_score > best_match_score:
            best_match_score = current_score
            best_match_line_index = i

    # Define a minimum score threshold (e.g., at least 1 keyword match now we use whole words)
    min_score_threshold = 1 # Adjusted threshold

    print(f"Best match score: {best_match_score} at index {best_match_line_index} (Threshold: {min_score_threshold})")

    if best_match_score >= min_score_threshold and best_match_line_index != -1:
        # Return the matched line as a simple answer.
        # TODO: Consider returning surrounding lines for better context.
        # Limit response length to avoid spamming Discord
        response = kb_lines[best_match_line_index]
        max_length = 1000 # Max characters for the response snippet (Increased from 500)
        if len(response) > max_length:
            response = response[:max_length] + "..."
        return f"Based on the knowledge base:\n>>> {response}"
    else:
        return None # No sufficiently relevant match found

# Example usage (for testing)
if __name__ == '__main__':
    load_knowledge_base() # Load it first
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
