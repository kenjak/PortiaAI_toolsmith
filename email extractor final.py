import re
from typing import List

def email_extractor_final(text: str) -> List[str]:
    """
    Extracts email addresses from a given string, converts them to lowercase, and returns them as a list.

    This function validates that the input is a string, uses a precompiled regular expression to find
    all email addresses within the text, converts each found email to lowercase, and returns them as a list.

    Parameters:
    text (str): The input string from which to extract email addresses.

    Returns:
    List[str]: A list of email addresses found in the input string, all converted to lowercase.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be of type str")

    # Precompiled regular expression for matching email addresses
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

    # Find all matches and convert them to lowercase
    emails = [email.lower() for email in email_pattern.findall(text)]

    return emails