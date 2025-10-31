"""Semantic chunking logic."""

import logging
import re
from typing import List, Dict, Any, Optional

from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from ..utils.exceptions import ProcessorError
from config.settings import Settings

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Semantic chunker for splitting documents intelligently."""

    def __init__(
        self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None
    ):
        """
        Initialize semantic chunker.

        Args:
            chunk_size: Maximum chunk size in tokens/characters
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size or Settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Settings.CHUNK_OVERLAP

        logger.debug(f"Initializing SemanticChunker (chunk_size={self.chunk_size}, overlap={self.chunk_overlap})")

        # Configure markdown header splitter
        self.headers_to_split_on = [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
            ("####", "h4"),
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )

        # Configure sentence/token splitter for further chunking
        self.sentence_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
        )
        
        logger.debug("SemanticChunker initialized")

    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk a document using semantic chunking approach.

        Args:
            document: Document dictionary with markdown_content and metadata

        Returns:
            List of chunk dictionaries
        """
        url = document.get("url", "")
        title = document.get("title", "Untitled")
        markdown_content = document.get("markdown_content", "")
        metadata = document.get("metadata", {})

        logger.debug(f"Chunking document: {title} ({len(markdown_content)} chars)")

        if not markdown_content:
            logger.warning(f"⚠️  No content to chunk for document: {title}")
            return []

        try:
            # Step 1: Split by markdown headers
            logger.debug("Step 1: Splitting by markdown headers...")
            header_chunks = self.markdown_splitter.split_text(markdown_content)
            logger.debug(f"Created {len(header_chunks)} header-based chunks")
        except Exception as e:
            logger.warning(f"⚠️  Error splitting document {title} by headers: {e}, using fallback")
            # Fallback: treat as a single chunk
            header_chunks = [
                {
                    "page_content": markdown_content,
                    "metadata": {"heading": title},
                }
            ]

        # Step 2: Further split large chunks by sentences/tokens
        logger.debug("Step 2: Splitting large chunks by sentences/tokens...")
        final_chunks = []
        for i, header_chunk in enumerate(header_chunks):
            chunk_content = (
                header_chunk.page_content
                if hasattr(header_chunk, "page_content")
                else header_chunk.get("content", "")
            )
            chunk_metadata = (
                header_chunk.metadata
                if hasattr(header_chunk, "metadata")
                else header_chunk.get("metadata", {})
            )

            # Skip empty chunks
            if not chunk_content.strip():
                continue

            # If chunk is small enough, keep as is
            if len(chunk_content) <= self.chunk_size:
                final_chunks.append(
                    {
                        "content": chunk_content,
                        "metadata": {
                            **chunk_metadata,
                            **metadata,
                            "chunk_index": len(final_chunks),
                        },
                    }
                )
                continue

            # Split larger chunks by sentences
            try:
                sentence_chunks = self.sentence_splitter.split_text(chunk_content)
            except Exception as e:
                logger.warning(f"Error splitting chunk by sentences: {e}, keeping as single chunk")
                sentence_chunks = [chunk_content]

            for j, sentence_chunk in enumerate(sentence_chunks):
                if sentence_chunk.strip():
                    final_chunks.append(
                        {
                            "content": sentence_chunk,
                            "metadata": {
                                **chunk_metadata,
                                **metadata,
                                "chunk_index": len(final_chunks),
                                "sub_chunk_index": j,
                            },
                        }
                    )

        # Add document-level metadata and generate chunk IDs
        logger.debug(f"Step 3: Adding metadata and generating IDs for {len(final_chunks)} chunks...")
        for i, chunk in enumerate(final_chunks):
            # Generate chunk ID from URL and index
            url_part = url.split("/")[-1] if url else "unknown"
            chunk["id"] = f"{url_part}_{i}"
            chunk["metadata"]["chunk_id"] = chunk["id"]
            chunk["metadata"]["doc_id"] = url

        logger.info(f"✅ Created {len(final_chunks)} chunks from {title[:40]}...")
        return final_chunks

    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple documents into chunks.

        Args:
            documents: List of document dictionaries

        Returns:
            List of all chunks from all documents
        """
        logger.info(f"Processing {len(documents)} documents into chunks...")
        all_chunks = []

        for idx, document in enumerate(documents):
            try:
                logger.debug(f"Processing document {idx + 1}/{len(documents)}: {document.get('title', 'Unknown')[:40]}...")
                document_chunks = self.chunk_document(document)
                all_chunks.extend(document_chunks)
            except Exception as e:
                logger.error(f"❌ Error chunking document {document.get('url', 'Unknown')}: {e}")
                raise ProcessorError(f"Failed to chunk document: {e}") from e

        logger.info(f"✅ Created {len(all_chunks)} total chunks from {len(documents)} documents")
        return all_chunks

