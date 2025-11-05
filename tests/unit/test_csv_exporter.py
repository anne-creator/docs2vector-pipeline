"""Unit tests for CSV exporter.

Testing Strategy:
- Core functionality tests use REAL embedding data from tests/.test_data/embeddings/
- Edge case tests use FAKE/minimal data for fast testing
- Output stored in tests/.test_data/csv_format/ for inspection
- Aligns with existing test patterns in the codebase
"""

import pytest
import csv
import json
import tempfile
from pathlib import Path
from src.export.csv_exporter import CSVExporter
from src.utils.exceptions import StorageError


class TestCSVExporter:
    """Test CSVExporter class with real data and edge cases."""

    # ========================================================================
    # CORE FUNCTIONALITY TESTS - Using Real Embedding Data
    # ========================================================================

    def test_export_real_embeddings(self):
        """Test exporting real embeddings from test data."""
        # Setup: Load real test data
        test_data_dir = Path(__file__).parent.parent / ".test_data"
        embeddings_dir = test_data_dir / "embeddings"
        csv_output_dir = test_data_dir / "csv_format"
        csv_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find a real embeddings file
        embedding_files = list(embeddings_dir.glob("embeddings_*.json"))
        if not embedding_files:
            pytest.skip("No real embedding data found in tests/.test_data/embeddings/")
        
        # Use the first embeddings file
        input_file = embedding_files[0]
        
        # Load embeddings
        with open(input_file, 'r', encoding='utf-8') as f:
            embeddings = json.load(f)
        
        # Export to CSV
        exporter = CSVExporter(output_dir=csv_output_dir)
        output_file = exporter.export_embeddings(
            embeddings,
            output_filename=f"test_{input_file.stem}.csv"
        )
        
        # Verify output
        assert output_file.exists()
        assert output_file.suffix == '.csv'
        
        # Verify CSV structure
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Should have same number of rows as input
            assert len(rows) == len(embeddings)
            
            # Check first row has all expected fields
            first_row = rows[0]
            expected_fields = [
                'id', 'content', 'source_url', 'document_title', 'last_updated',
                'breadcrumbs', 'related_links', 'scraped_at', 'category',
                'article_id', 'locale', 'page_hash', 'change_status',
                'chunk_index', 'sub_chunk_index', 'chunk_id', 'doc_id', 'embedding'
            ]
            for field in expected_fields:
                assert field in first_row, f"Missing field: {field}"
            
            # Verify data integrity
            assert first_row['id'] == embeddings[0]['id']
            assert first_row['content'] == embeddings[0]['content']
            
            # Verify embedding is JSON-encoded
            embedding_data = json.loads(first_row['embedding'])
            assert isinstance(embedding_data, list)
            assert len(embedding_data) == 384  # Standard embedding dimension

    def test_export_from_json_file_real_data(self):
        """Test exporting directly from real JSON file."""
        test_data_dir = Path(__file__).parent.parent / ".test_data"
        embeddings_dir = test_data_dir / "embeddings"
        csv_output_dir = test_data_dir / "csv_format"
        csv_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find a real embeddings file
        embedding_files = list(embeddings_dir.glob("embeddings_*.json"))
        if not embedding_files:
            pytest.skip("No real embedding data found")
        
        input_file = embedding_files[0]
        
        # Export
        exporter = CSVExporter(output_dir=csv_output_dir)
        output_file = exporter.export_from_json_file(input_file)
        
        # Verify
        assert output_file.exists()
        assert output_file.suffix == '.csv'
        
        # Count rows
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row_count = sum(1 for _ in reader)
            assert row_count > 0

    def test_batch_export_real_data(self):
        """Test batch exporting all real embedding files."""
        test_data_dir = Path(__file__).parent.parent / ".test_data"
        embeddings_dir = test_data_dir / "embeddings"
        csv_output_dir = test_data_dir / "csv_format"
        csv_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export all embeddings
        exporter = CSVExporter(output_dir=csv_output_dir)
        exported_files = exporter.batch_export_directory(embeddings_dir)
        
        # Verify
        assert len(exported_files) > 0
        for csv_file in exported_files:
            assert csv_file.exists()
            assert csv_file.suffix == '.csv'

    # ========================================================================
    # EDGE CASE TESTS - Using Minimal/Fake Data
    # ========================================================================

    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.exporter = CSVExporter(output_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test CSV exporter initialization."""
        exporter = CSVExporter(output_dir=self.temp_dir)
        assert exporter.output_dir == self.temp_dir
        assert exporter.output_dir.exists()

    def test_export_single_embedding(self):
        """Test exporting a single minimal embedding."""
        embeddings = [{
            'id': 'test_1',
            'content': 'Test content',
            'metadata': {
                'source_url': 'https://example.com',
                'document_title': 'Test Doc',
                'last_updated': '2024-01-01',
                'breadcrumbs': ['Home', 'Docs'],
                'related_links': [{'text': 'Link', 'url': 'https://example.com/link'}],
                'scraped_at': '2024-01-01T00:00:00',
                'category': ['test'],
                'article_id': '123',
                'locale': 'en-US',
                'page_hash': 'abc123',
                'change_status': 'new',
                'chunk_index': 0,
                'sub_chunk_index': 0,
                'chunk_id': 'test_1',
                'doc_id': 'https://example.com'
            },
            'embedding': [0.1] * 384
        }]
        
        output_file = self.exporter.export_embeddings(embeddings, 'test_single.csv')
        
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['id'] == 'test_1'
            assert rows[0]['content'] == 'Test content'

    def test_export_without_embedding_vector(self):
        """Test exporting without embedding vector (metadata only)."""
        embeddings = [{
            'id': 'test_1',
            'content': 'Test content',
            'metadata': {
                'source_url': 'https://example.com',
                'document_title': 'Test',
                'chunk_id': 'test_1'
            },
            'embedding': [0.1] * 384
        }]
        
        output_file = self.exporter.export_embeddings(
            embeddings,
            'test_no_embedding.csv',
            include_embedding=False
        )
        
        # Verify embedding column is not in CSV
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            assert 'embedding' not in fieldnames
            
            rows = list(reader)
            assert len(rows) == 1

    def test_export_empty_list(self):
        """Test exporting empty embeddings list."""
        result = self.exporter.export_embeddings([], 'test_empty.csv')
        assert result is None

    def test_export_missing_metadata_fields(self):
        """Test exporting with missing metadata fields."""
        embeddings = [{
            'id': 'test_1',
            'content': 'Test content',
            'metadata': {
                'source_url': 'https://example.com',
                # Missing many fields
            },
            'embedding': [0.1] * 384
        }]
        
        output_file = self.exporter.export_embeddings(embeddings, 'test_partial.csv')
        
        # Verify it still exports with empty values
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['id'] == 'test_1'
            assert rows[0]['document_title'] == ''  # Should be empty

    def test_export_special_characters_in_content(self):
        """Test exporting content with special characters and newlines."""
        embeddings = [{
            'id': 'test_1',
            'content': 'Test with "quotes", commas, and\nnewlines\ttabs',
            'metadata': {
                'source_url': 'https://example.com',
                'document_title': 'Test "Title" with, special chars',
                'chunk_id': 'test_1'
            },
            'embedding': [0.1] * 384
        }]
        
        output_file = self.exporter.export_embeddings(embeddings, 'test_special.csv')
        
        # Verify CSV properly handles special characters
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert 'quotes' in rows[0]['content']
            assert 'newlines' in rows[0]['content']

    def test_export_large_content(self):
        """Test exporting with very large content field."""
        large_content = 'X' * 10000  # 10K characters
        embeddings = [{
            'id': 'test_1',
            'content': large_content,
            'metadata': {
                'source_url': 'https://example.com',
                'chunk_id': 'test_1'
            },
            'embedding': [0.1] * 384
        }]
        
        output_file = self.exporter.export_embeddings(embeddings, 'test_large.csv')
        
        # Verify large content is handled
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows[0]['content']) == 10000

    def test_export_nonexistent_json_file(self):
        """Test exporting from non-existent JSON file."""
        with pytest.raises(StorageError, match="not found"):
            self.exporter.export_from_json_file(Path('/nonexistent/file.json'))

    def test_export_invalid_json_file(self):
        """Test exporting from invalid JSON file."""
        # Create invalid JSON file
        invalid_json = self.temp_dir / 'invalid.json'
        with open(invalid_json, 'w') as f:
            f.write('{ invalid json }')
        
        with pytest.raises(StorageError, match="Invalid JSON"):
            self.exporter.export_from_json_file(invalid_json)

    def test_batch_export_empty_directory(self):
        """Test batch export with empty directory."""
        empty_dir = self.temp_dir / 'empty'
        empty_dir.mkdir()
        
        exported_files = self.exporter.batch_export_directory(empty_dir)
        assert len(exported_files) == 0

    def test_batch_export_nonexistent_directory(self):
        """Test batch export with non-existent directory."""
        with pytest.raises(StorageError, match="not found"):
            self.exporter.batch_export_directory(Path('/nonexistent/dir'))

    def test_batch_export_mixed_files(self):
        """Test batch export with valid and invalid files."""
        # Create test directory with mixed files
        test_dir = self.temp_dir / 'mixed'
        test_dir.mkdir()
        
        # Valid JSON file
        valid_embeddings = [{
            'id': 'test_1',
            'content': 'Test',
            'metadata': {'source_url': 'https://example.com'},
            'embedding': [0.1] * 384
        }]
        valid_file = test_dir / 'valid.json'
        with open(valid_file, 'w') as f:
            json.dump(valid_embeddings, f)
        
        # Invalid JSON file
        invalid_file = test_dir / 'invalid.json'
        with open(invalid_file, 'w') as f:
            f.write('{ invalid }')
        
        # Export - should handle error gracefully
        exported_files = self.exporter.batch_export_directory(test_dir)
        
        # Should export only the valid file
        assert len(exported_files) == 1
        assert exported_files[0].exists()

    def test_convert_record_with_empty_arrays(self):
        """Test converting record with empty arrays in metadata."""
        record = {
            'id': 'test_1',
            'content': 'Test',
            'metadata': {
                'breadcrumbs': [],
                'related_links': [],
                'category': [],
                'source_url': 'https://example.com'
            },
            'embedding': [0.1] * 384
        }
        
        row = self.exporter._convert_record_to_row(record)
        
        assert row['breadcrumbs'] == '[]'
        assert row['related_links'] == '[]'
        assert row['category'] == '[]'

    def test_convert_record_with_complex_nested_data(self):
        """Test converting record with complex nested structures."""
        record = {
            'id': 'test_1',
            'content': 'Test',
            'metadata': {
                'breadcrumbs': ['Home', 'Docs', 'Section'],
                'related_links': [
                    {'text': 'Link 1', 'url': 'https://example.com/1'},
                    {'text': 'Link 2', 'url': 'https://example.com/2'}
                ],
                'category': ['cat1', 'cat2'],
                'source_url': 'https://example.com'
            },
            'embedding': [0.1] * 384
        }
        
        row = self.exporter._convert_record_to_row(record)
        
        # Verify JSON encoding of arrays
        breadcrumbs = json.loads(row['breadcrumbs'])
        assert breadcrumbs == ['Home', 'Docs', 'Section']
        
        related_links = json.loads(row['related_links'])
        assert len(related_links) == 2
        assert related_links[0]['text'] == 'Link 1'

    def test_export_multiple_embeddings(self):
        """Test exporting multiple embeddings."""
        embeddings = [
            {
                'id': f'test_{i}',
                'content': f'Test content {i}',
                'metadata': {
                    'source_url': f'https://example.com/{i}',
                    'document_title': f'Doc {i}',
                    'chunk_id': f'test_{i}'
                },
                'embedding': [0.1 * i] * 384
            }
            for i in range(10)
        ]
        
        output_file = self.exporter.export_embeddings(embeddings, 'test_multiple.csv')
        
        # Verify all records exported
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 10
            assert rows[0]['id'] == 'test_0'
            assert rows[9]['id'] == 'test_9'

    def test_export_with_unicode_content(self):
        """Test exporting with Unicode characters."""
        embeddings = [{
            'id': 'test_1',
            'content': 'Test with unicode: 你好 مرحبا שלום',
            'metadata': {
                'source_url': 'https://example.com',
                'document_title': 'Unicode тест',
                'chunk_id': 'test_1'
            },
            'embedding': [0.1] * 384
        }]
        
        output_file = self.exporter.export_embeddings(embeddings, 'test_unicode.csv')
        
        # Verify Unicode is preserved
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert '你好' in rows[0]['content']
            assert 'Unicode тест' in rows[0]['document_title']

