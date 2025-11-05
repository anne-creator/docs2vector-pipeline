"""CSV export service for embeddings."""

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.exceptions import StorageError
from config.settings import Settings

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports embeddings from JSON format to CSV for RAG systems."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize CSV exporter.

        Args:
            output_dir: Directory for CSV output (defaults to Settings.DATA_DIR / 'csv_export')
        """
        if output_dir is None:
            self.output_dir = Settings.DATA_DIR / "csv_export"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"CSVExporter initialized (output_dir: {self.output_dir})")

    def export_embeddings(
        self,
        embeddings: List[Dict[str, Any]],
        output_filename: Optional[str] = None,
        include_embedding: bool = True
    ) -> Path:
        """
        Export embeddings to CSV file.

        Args:
            embeddings: List of embedding dictionaries with 'id', 'content', 'metadata', 'embedding'
            output_filename: Optional output filename (defaults to timestamped name)
            include_embedding: Whether to include embedding vector in CSV (default: True)

        Returns:
            Path to exported CSV file

        Raises:
            StorageError: If export fails
        """
        if not embeddings:
            logger.warning("⚠️  No embeddings to export")
            return None

        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"embeddings_{timestamp}.csv"

        output_path = self.output_dir / output_filename
        
        try:
            logger.info(f"Exporting {len(embeddings)} embeddings to CSV...")
            logger.debug(f"Output path: {output_path}")
            
            # Define CSV fieldnames
            fieldnames = [
                'id', 'content', 'source_url', 'document_title', 'last_updated',
                'breadcrumbs', 'related_links', 'scraped_at', 'category',
                'article_id', 'locale', 'page_hash', 'change_status',
                'chunk_index', 'sub_chunk_index', 'chunk_id', 'doc_id'
            ]
            
            if include_embedding:
                fieldnames.append('embedding')
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for i, record in enumerate(embeddings):
                    try:
                        row = self._convert_record_to_row(record, include_embedding)
                        writer.writerow(row)
                    except Exception as e:
                        logger.error(f"❌ Error converting record {i} (id: {record.get('id', 'unknown')}): {e}")
                        raise StorageError(f"Failed to convert record {i}: {e}") from e
            
            logger.info(f"✅ Successfully exported {len(embeddings)} embeddings to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error exporting embeddings to CSV: {e}")
            raise StorageError(f"Failed to export embeddings: {e}") from e

    def _convert_record_to_row(
        self,
        record: Dict[str, Any],
        include_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        Convert an embedding record to a CSV row.

        Args:
            record: Embedding record with 'id', 'content', 'metadata', 'embedding'
            include_embedding: Whether to include embedding vector

        Returns:
            Dictionary representing CSV row
        """
        metadata = record.get('metadata', {})
        
        row = {
            'id': record.get('id', ''),
            'content': record.get('content', ''),
            'source_url': metadata.get('source_url', ''),
            'document_title': metadata.get('document_title', ''),
            'last_updated': metadata.get('last_updated', ''),
            'breadcrumbs': json.dumps(metadata.get('breadcrumbs', [])),
            'related_links': json.dumps(metadata.get('related_links', [])),
            'scraped_at': metadata.get('scraped_at', ''),
            'category': json.dumps(metadata.get('category', [])),
            'article_id': metadata.get('article_id', ''),
            'locale': metadata.get('locale', ''),
            'page_hash': metadata.get('page_hash', ''),
            'change_status': metadata.get('change_status', ''),
            'chunk_index': metadata.get('chunk_index', ''),
            'sub_chunk_index': metadata.get('sub_chunk_index', ''),
            'chunk_id': metadata.get('chunk_id', ''),
            'doc_id': metadata.get('doc_id', ''),
        }
        
        if include_embedding:
            embedding = record.get('embedding', [])
            row['embedding'] = json.dumps(embedding)
        
        return row

    def export_from_json_file(
        self,
        json_file_path: Path,
        output_filename: Optional[str] = None,
        include_embedding: bool = True
    ) -> Path:
        """
        Load embeddings from JSON file and export to CSV.

        Args:
            json_file_path: Path to JSON file containing embeddings
            output_filename: Optional output filename
            include_embedding: Whether to include embedding vector

        Returns:
            Path to exported CSV file

        Raises:
            StorageError: If loading or exporting fails
        """
        json_file_path = Path(json_file_path)
        
        if not json_file_path.exists():
            raise StorageError(f"JSON file not found: {json_file_path}")
        
        try:
            logger.info(f"Loading embeddings from {json_file_path}...")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                embeddings = json.load(f)
            
            if not isinstance(embeddings, list):
                raise StorageError(f"Expected list of embeddings, got {type(embeddings)}")
            
            logger.info(f"Loaded {len(embeddings)} embeddings from JSON")
            
            # Use input filename as base for output if not specified
            if output_filename is None:
                base_name = json_file_path.stem
                output_filename = f"{base_name}.csv"
            
            return self.export_embeddings(embeddings, output_filename, include_embedding)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON format in {json_file_path}: {e}")
            raise StorageError(f"Invalid JSON file: {e}") from e
        except Exception as e:
            logger.error(f"❌ Error loading JSON file: {e}")
            raise StorageError(f"Failed to load JSON file: {e}") from e

    def batch_export_directory(
        self,
        input_dir: Path,
        pattern: str = "*.json",
        include_embedding: bool = True
    ) -> List[Path]:
        """
        Export all JSON files in a directory to CSV.

        Args:
            input_dir: Directory containing JSON embedding files
            pattern: File pattern to match (default: "*.json")
            include_embedding: Whether to include embedding vectors

        Returns:
            List of paths to exported CSV files

        Raises:
            StorageError: If batch export fails
        """
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            raise StorageError(f"Input directory not found: {input_dir}")
        
        json_files = list(input_dir.glob(pattern))
        
        if not json_files:
            logger.warning(f"⚠️  No files matching '{pattern}' found in {input_dir}")
            return []
        
        logger.info(f"Found {len(json_files)} JSON files to export")
        exported_files = []
        
        for json_file in json_files:
            try:
                logger.info(f"Processing {json_file.name}...")
                csv_path = self.export_from_json_file(
                    json_file,
                    include_embedding=include_embedding
                )
                exported_files.append(csv_path)
            except Exception as e:
                logger.error(f"❌ Failed to export {json_file.name}: {e}")
                # Continue with other files
                continue
        
        logger.info(f"✅ Successfully exported {len(exported_files)}/{len(json_files)} files")
        return exported_files

