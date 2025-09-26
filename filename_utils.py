#!/usr/bin/env python3
"""
Filename Utilities
Consistent filename sanitization for PDF generation and email lookup
"""

import re
import unicodedata

def sanitize_filename(text):
    """
    Sanitize text for safe filename creation with proper Unicode handling
    """
    if not text:
        return ''
    
    # Convert to string and strip whitespace
    text = str(text).strip()
    
    # Normalize Unicode characters (NFD = decomposed form)
    # This converts é to e + combining accent, then we can remove the accent
    normalized = unicodedata.normalize('NFD', text)
    
    # Remove combining characters (accents) and keep only ASCII
    ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    # Replace special characters with underscores (including / for policy numbers)
    # This ensures 00520/0001149 becomes 00520_0001149
    clean_text = re.sub(r'[^\w\s-]', '_', ascii_text)
    
    # Replace spaces with underscores
    clean_text = clean_text.replace(' ', '_')
    
    # Remove multiple consecutive underscores
    clean_text = re.sub(r'_+', '_', clean_text)
    
    # Remove leading/trailing underscores
    clean_text = clean_text.strip('_')
    
    return clean_text

def create_pdf_filename(policy_no, name):
    """
    Create consistent PDF filename from policy number and name
    """
    safe_policy = sanitize_filename(str(policy_no))
    safe_name = sanitize_filename(name)
    
    return f"{safe_policy}_{safe_name}.pdf"

# Test the function
if __name__ == "__main__":
    test_cases = [
        "André",
        "Jean-François", 
        "José María",
        "François Müller",
        "O'Connor",
        "Smith & Jones",
        "00520/0001149",  # Policy number test
        "00840/0000261"   # Another policy number test
    ]
    
    print("Testing filename sanitization:")
    for name in test_cases:
        sanitized = sanitize_filename(name)
        print(f"'{name}' -> '{sanitized}'")