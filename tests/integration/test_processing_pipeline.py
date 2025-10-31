"""Integration tests for the full processing pipeline.

Testing Strategy:
- ALL integration tests use REAL scraped data from tests/.test_data/
- Tests validate the complete pipeline: scraping -> preprocessing -> chunking -> embeddings
- Run scripts/test_scraper_10pages.py first to generate real test data
"""

import pytest
from pathlib import Path

from src.processor.preprocessor import Preprocessor
from src.processor.chunker import SemanticChunker
from src.embeddings.generator import EmbeddingGenerator
from src.storage.file_manager import FileManager


@pytest.mark.integration
class TestProcessingPipelineIntegration:
    """Integration tests for the complete processing pipeline with real data."""

    def test_full_pipeline_single_document(self, single_scraped_item, tmp_path):
        """Test complete pipeline: preprocess -> chunk -> embed with real document."""
        # Initialize components
        preprocessor = Preprocessor()
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        file_manager = FileManager(base_dir=tmp_path)
        file_manager.ensure_directories()
        
        # Step 1: Preprocess
        markdown = preprocessor.process(
            single_scraped_item["html_content"],
            single_scraped_item.get("text_content")
        )
        
        processed_doc = {
            "url": single_scraped_item["url"],
            "title": single_scraped_item["title"],
            "markdown_content": markdown,
            "metadata": single_scraped_item.get("metadata", {})
        }
        
        # Step 2: Chunk
        chunks = chunker.chunk_document(processed_doc)
        assert len(chunks) > 0, "Should create chunks from real document"
        
        # Step 3: Generate embeddings
        chunks_with_embeddings = generator.process_chunks(chunks)
        assert len(chunks_with_embeddings) == len(chunks)
        assert all("embedding" in chunk for chunk in chunks_with_embeddings)
        
        # Step 4: Save to file system
        file_manager.save_processed_data([processed_doc])
        file_manager.save_chunks(chunks_with_embeddings)
        
        # Verify files were created
        processed_files = list((tmp_path / "processed").glob("*.json"))
        chunk_files = list((tmp_path / "chunks").glob("*.json"))
        
        assert len(processed_files) > 0, "Should save processed data"
        assert len(chunk_files) > 0, "Should save chunks"

    def test_full_pipeline_batch_processing(self, multiple_scraped_items, tmp_path):
        """Test complete pipeline with multiple real documents."""
        # Initialize components
        preprocessor = Preprocessor()
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        file_manager = FileManager(base_dir=tmp_path)
        file_manager.ensure_directories()
        
        processed_docs = []
        all_chunks = []
        
        # Process each document
        for item in multiple_scraped_items:
            # Preprocess
            markdown = preprocessor.process(
                item["html_content"],
                item.get("text_content")
            )
            
            processed_doc = {
                "url": item["url"],
                "title": item["title"],
                "markdown_content": markdown,
                "metadata": item.get("metadata", {})
            }
            processed_docs.append(processed_doc)
            
            # Chunk
            chunks = chunker.chunk_document(processed_doc)
            all_chunks.extend(chunks)
        
        # Verify processing
        assert len(processed_docs) == len(multiple_scraped_items)
        assert len(all_chunks) > 0
        assert len(all_chunks) >= len(multiple_scraped_items), \
            "Should have at least one chunk per document"
        
        # Generate embeddings for all chunks
        chunks_with_embeddings = generator.process_chunks(all_chunks)
        assert len(chunks_with_embeddings) == len(all_chunks)
        
        # Save everything
        file_manager.save_processed_data(processed_docs)
        file_manager.save_chunks(chunks_with_embeddings)
        
        # Verify saved data
        saved_processed = file_manager.load_processed_data()
        saved_chunks = file_manager.load_chunks()
        
        assert len(saved_processed) == len(processed_docs)
        assert len(saved_chunks) == len(chunks_with_embeddings)

    def test_pipeline_preserves_metadata(self, single_scraped_item, tmp_path):
        """Test that metadata is preserved throughout the pipeline."""
        preprocessor = Preprocessor()
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
        
        # Extract original metadata
        original_url = single_scraped_item["url"]
        original_title = single_scraped_item["title"]
        original_metadata = single_scraped_item.get("metadata", {})
        
        # Process
        markdown = preprocessor.process(
            single_scraped_item["html_content"],
            single_scraped_item.get("text_content")
        )
        
        processed_doc = {
            "url": original_url,
            "title": original_title,
            "markdown_content": markdown,
            "metadata": original_metadata
        }
        
        # Chunk
        chunks = chunker.chunk_document(processed_doc)
        
        # Verify metadata preservation
        for chunk in chunks:
            assert chunk["metadata"]["source_url"] == original_url
            assert chunk["metadata"]["document_title"] == original_title
            # Original metadata should be in the chunk metadata
            assert "doc_id" in chunk["metadata"] or "source_url" in chunk["metadata"]

    def test_pipeline_handles_all_scraped_documents(self, all_scraped_items, tmp_path):
        """Test pipeline can handle all documents from a scraper run (~10 docs)."""
        preprocessor = Preprocessor()
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
        
        # Process all documents
        all_processed = []
        all_chunks = []
        
        for item in all_scraped_items:
            try:
                markdown = preprocessor.process(
                    item["html_content"],
                    item.get("text_content")
                )
                
                processed_doc = {
                    "url": item["url"],
                    "title": item["title"],
                    "markdown_content": markdown,
                    "metadata": item.get("metadata", {})
                }
                all_processed.append(processed_doc)
                
                chunks = chunker.chunk_document(processed_doc)
                all_chunks.extend(chunks)
                
            except Exception as e:
                pytest.fail(f"Failed to process document {item.get('url')}: {e}")
        
        # Verify all documents were processed
        assert len(all_processed) == len(all_scraped_items), \
            "All scraped documents should be processed successfully"
        assert len(all_chunks) > 0, "Should create chunks from all documents"
        
        # Verify all URLs are unique
        urls = [doc["url"] for doc in all_processed]
        assert len(urls) == len(set(urls)), "All processed documents should have unique URLs"
        
        # Verify chunk IDs are unique
        chunk_ids = [chunk["id"] for chunk in all_chunks]
        assert len(chunk_ids) == len(set(chunk_ids)), "All chunk IDs should be unique"

    def test_pipeline_chunk_content_quality(self, multiple_scraped_items):
        """Test that chunked content maintains quality and readability."""
        preprocessor = Preprocessor()
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
        
        for item in multiple_scraped_items[:3]:  # Test first 3 documents
            markdown = preprocessor.process(
                item["html_content"],
                item.get("text_content")
            )
            
            processed_doc = {
                "url": item["url"],
                "title": item["title"],
                "markdown_content": markdown,
                "metadata": {"source_url": item["url"]}
            }
            
            chunks = chunker.chunk_document(processed_doc)
            
            # Verify chunk quality
            for chunk in chunks:
                content = chunk["content"]
                
                # Content should not be empty
                assert len(content.strip()) > 0, "Chunks should have content"
                
                # Content should be readable (not just HTML tags or garbage)
                assert not content.startswith("<"), "Content should be markdown, not HTML"
                
                # Should have some words
                word_count = len(content.split())
                assert word_count > 5, "Chunks should have meaningful content"

