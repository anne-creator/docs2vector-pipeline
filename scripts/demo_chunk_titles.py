#!/usr/bin/env python3
"""
Demonstration script to show the new chunk_title functionality.

This script processes a sample document and displays the chunk titles
that are automatically extracted from the markdown header hierarchy.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.processor.chunker import SemanticChunker
from src.processor.preprocessor import Preprocessor


def main():
    """Demonstrate chunk title extraction."""
    print("=" * 80)
    print("Chunk Title Extraction Demonstration")
    print("=" * 80)
    print()

    # Create sample document with multiple header levels
    sample_markdown = """# Amazon Seller Account Settings

Account settings allow you to manage your seller profile and preferences.

## Payment Information

You can update your payment methods in the account settings.

### Bank Account Details

Enter your routing number and account number to receive payments.

### Credit Card Information

Add or update your credit card for subscription payments.

## Business Information

Keep your business details up to date for compliance.

### Tax Information

Update your tax identification number and business structure.

### Legal Address

Ensure your business address matches official records.

## Security Settings

Protect your account with two-factor authentication.

### Two-Factor Authentication

Enable 2FA to add an extra layer of security to your account.

### Password Management

Change your password regularly and use a strong combination.
"""

    # Create document
    document = {
        "url": "https://example.com/help/account-settings",
        "title": "Amazon Seller Account Settings",
        "markdown_content": sample_markdown,
        "metadata": {
            "source_url": "https://example.com/help/account-settings",
            "document_title": "Amazon Seller Account Settings",
        }
    }

    # Initialize chunker
    chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)

    # Process document
    print(f"Processing document: {document['title']}")
    print(f"Document length: {len(document['markdown_content'])} characters")
    print()

    chunks = chunker.chunk_document(document)

    print(f"✅ Created {len(chunks)} chunks")
    print()
    print("=" * 80)
    print("Chunk Titles Extracted:")
    print("=" * 80)
    print()

    # Display chunk titles
    for i, chunk in enumerate(chunks):
        chunk_title = chunk["metadata"].get("chunk_title", "N/A")
        content_preview = chunk["content"][:100].replace("\n", " ")
        
        print(f"Chunk {i + 1}:")
        print(f"  📌 Chunk Title: {chunk_title}")
        print(f"  📝 Content Preview: {content_preview}...")
        print(f"  📊 Length: {len(chunk['content'])} chars")
        
        # Show header hierarchy if available
        headers = []
        for level in ["h1", "h2", "h3", "h4"]:
            if level in chunk["metadata"] and chunk["metadata"][level]:
                headers.append(f"{level.upper()}: {chunk['metadata'][level]}")
        
        if headers:
            print(f"  🔖 Headers: {' > '.join(headers)}")
        
        print()

    print("=" * 80)
    print("Benefits of Chunk Titles:")
    print("=" * 80)
    print("""
✅ Each chunk has a descriptive, contextual title
✅ Titles use markdown header hierarchy for context
✅ Nested sections show parent > child relationships
✅ Improves RAG retrieval by matching against chunk titles
✅ Sub-chunks get part numbers (e.g., "Section (Part 1)")
✅ Falls back to document title when no headers available
    """)


if __name__ == "__main__":
    main()

