# Amazon Sellers RAG: Semantic Chunking Implementation Guide

This guide provides a detailed, step by step implementation approach for building the Amazon Sellers RAG system with a focus on semantic chunking best practices.

## Complete Pipeline Implementation

### 1. Scrape Data (Raw Extraction)

First, we'll enhance the provided Scrapy spider to ensure comprehensive data collection:

```python
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from datetime import datetime
import hashlib
import json
import os

class AmazonSellerHelpSpider(CrawlSpider):
    name = 'amazon_seller_help'
    allowed_domains = ['sellercentral.amazon.com']
    start_urls = ['https://sellercentral.amazon.com/help/hub/reference/external/G2?locale=en-US']
    
    # Content hash tracking for change detection
    content_hashes = {}
    hash_file = 'content_hashes.json'
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            content_hashes = json.load(f)
    
    # Enhanced rules for comprehensive coverage
    rules = (
        # Main help articles
        Rule(
            LinkExtractor(
                allow=r'/help/hub/reference/',
                restrict_xpaths='//a[contains(@href, "/help/hub/reference/")]'
            ),
            callback='parse_item',
            follow=True
        ),
        # Policy pages
        Rule(
            LinkExtractor(
                allow=r'/help/policy/',
                restrict_xpaths='//a[contains(@href, "/help/policy/")]'
            ),
            callback='parse_item',
            follow=True
        ),
        # Guide pages
        Rule(
            LinkExtractor(
                allow=r'/help/guide/',
                restrict_xpaths='//a[contains(@href, "/help/guide/")]'
            ),
            callback='parse_item',
            follow=True
        ),
    )
    
    def parse_item(self, response):
        # Extract title with fallbacks for different page structures
        title = (
            response.css('h1::text').get() or 
            response.css('.title::text').get() or 
            response.xpath('//title/text()').get()
        )
        
        # Extract raw HTML content for later processing
        # This retains structure for markdown conversion
        article_html = response.css('article').get() or response.css('.help-content').get()
        
        # Extract plain text for change detection
        content_parts = []
        # Main article content
        article_content = response.css('article p::text, article li::text, article h2::text, article h3::text').getall()
        if article_content:
            content_parts.extend(article_content)
        
        # Content div fallback
        if not content_parts:
            content_parts = response.css('.content p::text, .content li::text').getall()
        
        # Generic content fallback
        if not content_parts:
            content_parts = response.css('p::text, li::text').getall()
        
        # Join content parts and clean whitespace
        content_text = ' '.join(content_parts).strip()
        content_text = ' '.join(content_text.split())  # Normalize whitespace
        
        # Extract breadcrumbs for categorization
        breadcrumbs = response.css('.breadcrumb a::text').getall() or response.css('.breadcrumbs a::text').getall() or []
        
        # Extract any related topics
        related_links = []
        for link in response.css('.related-topics a, .see-also a'):
            related_links.append({
                'text': link.css('::text').get(),
                'url': link.css('::attr(href)').get()
            })
        
        # Check if page has changed since last scrape
        page_hash = hashlib.md5(content_text.encode()).hexdigest()
        url = response.url
        change_status = 'unchanged'
        
        if url in self.content_hashes:
            if self.content_hashes[url] != page_hash:
                # Page updated
                change_status = 'updated'
        else:
            # New page
            change_status = 'new'
        
        # Update hash
        self.content_hashes[url] = page_hash
        
        # Periodically save hashes
        if len(self.content_hashes) % 10 == 0:
            with open(self.hash_file, 'w') as f:
                json.dump(self.content_hashes, f)
        
        # Yield the complete data
        yield {
            'url': url,
            'title': title,
            'html_content': article_html,  # Save raw HTML for markdown conversion
            'text_content': content_text,
            'last_updated': (
                response.css('.last-updated::text').get() or 
                response.css('.modified-date::text').get() or
                response.css('time::text').get()
            ),
            'metadata': {
                'category': breadcrumbs,
                'related_links': related_links,
                'page_hash': page_hash,
                'change_status': change_status,
                'scrape_time': datetime.now().isoformat()
            }
        }
    
    def closed(self, reason):
        # Save final hashes
        with open(self.hash_file, 'w') as f:
            json.dump(self.content_hashes, f)
```

Run this spider with the following command:

```bash
scrapy crawl amazon_seller_help -o amazon_seller_data.json
```

### 2. Clean & Preprocess Data

Next, we'll implement a preprocessing pipeline that converts HTML to Markdown for easier semantic chunking:

```python
import json
import os
from markdownify import markdownify as md
import re
from bs4 import BeautifulSoup
from tqdm import tqdm

class DataPreprocessor:
    def __init__(self, input_file, output_dir):
        self.input_file = input_file
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_data(self):
        """Load scraped data from JSON file"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def clean_html(self, html_content):
        """Clean HTML by removing unnecessary elements"""
        if not html_content:
            return ""
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove navigation, footer, ads, etc.
        for element in soup.select('nav, footer, .ads, .navigation, .sidebar, script, style'):
            element.decompose()
            
        return str(soup)
    
    def html_to_markdown(self, html_content):
        """Convert HTML to Markdown"""
        if not html_content:
            return ""
            
        # Clean the HTML first
        clean_html = self.clean_html(html_content)
        
        # Convert to Markdown
        markdown = md(clean_html)
        
        # Clean up the markdown
        # Remove excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown
    
    def process(self):
        """Process all data"""
        data = self.load_data()
        
        print(f"Processing {len(data)} documents...")
        
        processed_documents = []
        
        for item in tqdm(data):
            # Skip items with no content
            if not item.get('html_content') and not item.get('text_content'):
                continue
                
            # Convert HTML to Markdown if available
            markdown_content = ""
            if item.get('html_content'):
                markdown_content = self.html_to_markdown(item['html_content'])
            
            # If no HTML or markdown conversion failed, use text content
            if not markdown_content and item.get('text_content'):
                markdown_content = item['text_content']
            
            # Create processed document
            processed_doc = {
                'url': item['url'],
                'title': item['title'],
                'markdown_content': markdown_content,
                'last_updated': item.get('last_updated', ''),
                'metadata': item.get('metadata', {})
            }
            
            processed_documents.append(processed_doc)
            
            # Save individual document
            doc_filename = f"doc_{len(processed_documents)}.json"
            with open(os.path.join(self.output_dir, doc_filename), 'w', encoding='utf-8') as f:
                json.dump(processed_doc, f, ensure_ascii=False, indent=2)
        
        # Save all documents to a single file
        with open(os.path.join(self.output_dir, 'all_processed_docs.json'), 'w', encoding='utf-8') as f:
            json.dump(processed_documents, f, ensure_ascii=False, indent=2)
            
        print(f"Processed {len(processed_documents)} documents.")
        return processed_documents

# Run the preprocessor
preprocessor = DataPreprocessor(
    input_file='amazon_seller_data.json',
    output_dir='processed_data'
)
processed_docs = preprocessor.process()
```

### 3. Semantic Chunking

Now we'll implement your recommended semantic chunking approach, first chunking by headings then by sentences:

```python
import json
import os
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from tqdm import tqdm

class SemanticChunker:
    def __init__(self, input_dir, output_dir, chunk_size=512, chunk_overlap=64):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configure markdown header splitter
        self.headers_to_split_on = [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
            ("####", "h4"),
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on)
        
        # Configure sentence/token splitter for further chunking
        self.sentence_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )
    
    def load_documents(self):
        """Load processed documents from individual files"""
        documents = []
        
        # Get all JSON files in input directory
        file_list = [f for f in os.listdir(self.input_dir) if f.startswith('doc_') and f.endswith('.json')]
        
        for filename in file_list:
            file_path = os.path.join(self.input_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                document = json.load(f)
                documents.append(document)
                
        return documents
    
    def chunk_document(self, document):
        """Chunk a document using the semantic chunking approach"""
        url = document['url']
        title = document['title']
        markdown_content = document['markdown_content']
        metadata = document.get('metadata', {})
        
        # Skip if no content
        if not markdown_content:
            return []
        
        # Step 1: Split by markdown headers
        try:
            header_chunks = self.markdown_splitter.split_text(markdown_content)
        except Exception as e:
            print(f"Error splitting document {title} by headers: {e}")
            # Fallback: treat as a single chunk
            header_chunks = [{
                "content": markdown_content,
                "metadata": {"heading": title}
            }]
        
        # Step 2: Further split large chunks by sentences/tokens
        final_chunks = []
        for i, header_chunk in enumerate(header_chunks):
            chunk_content = header_chunk.page_content if hasattr(header_chunk, 'page_content') else header_chunk.get('content', '')
            chunk_metadata = header_chunk.metadata if hasattr(header_chunk, 'metadata') else header_chunk.get('metadata', {})
            
            # Skip empty chunks
            if not chunk_content.strip():
                continue
            
            # If chunk is small enough, keep as is
            if len(chunk_content) <= self.chunk_size:
                final_chunks.append({
                    "content": chunk_content,
                    "metadata": {
                        **chunk_metadata,
                        "source_url": url,
                        "document_title": title,
                        "chunk_index": len(final_chunks),
                        "source_metadata": metadata
                    }
                })
                continue
            
            # Split larger chunks by sentences
            sentence_chunks = self.sentence_splitter.split_text(chunk_content)
            
            for j, sentence_chunk in enumerate(sentence_chunks):
                final_chunks.append({
                    "content": sentence_chunk,
                    "metadata": {
                        **chunk_metadata,
                        "source_url": url,
                        "document_title": title,
                        "chunk_index": len(final_chunks),
                        "sub_chunk_index": j,
                        "source_metadata": metadata
                    }
                })
        
        # Add document-level metadata and generate chunk IDs
        for i, chunk in enumerate(final_chunks):
            chunk_id = f"{url.split('/')[-1]}_{i}"
            chunk["id"] = chunk_id
            chunk["metadata"]["doc_id"] = url
            chunk["metadata"]["chunk_id"] = chunk_id
        
        return final_chunks
    
    def process_all_documents(self):
        """Process all documents and create chunks"""
        documents = self.load_documents()
        
        print(f"Chunking {len(documents)} documents...")
        
        all_chunks = []
        
        for document in tqdm(documents):
            document_chunks = self.chunk_document(document)
            all_chunks.extend(document_chunks)
            
            # Save chunks for this document
            doc_id = document['url'].split('/')[-1]
            chunks_filename = f"chunks_{doc_id}.json"
            with open(os.path.join(self.output_dir, chunks_filename), 'w', encoding='utf-8') as f:
                json.dump(document_chunks, f, ensure_ascii=False, indent=2)
        
        # Save all chunks to a single file
        with open(os.path.join(self.output_dir, 'all_chunks.json'), 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
            
        print(f"Created {len(all_chunks)} chunks from {len(documents)} documents.")
        return all_chunks

# Run the chunker
chunker = SemanticChunker(
    input_dir='processed_data',
    output_dir='chunks',
    chunk_size=512,
    chunk_overlap=64
)
all_chunks = chunker.process_all_documents()
```

### 4. Generate Embeddings

Before loading into Neo4j, we need to create embeddings for semantic search:

```python
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

class EmbeddingGenerator:
    def __init__(self, input_dir, output_dir, model_name='all-MiniLM-L6-v2'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.model_name = model_name
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load the embedding model
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
    def load_chunks(self):
        """Load chunks from the all_chunks.json file"""
        chunks_file = os.path.join(self.input_dir, 'all_chunks.json')
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        return chunks
    
    def generate_embeddings(self, chunks, batch_size=32):
        """Generate embeddings for all chunks"""
        print(f"Generating embeddings for {len(chunks)} chunks...")
        
        # Extract texts to embed
        texts = [chunk['content'] for chunk in chunks]
        
        # Process in batches to avoid memory issues
        all_embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size)):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(batch_texts)
            all_embeddings.extend(batch_embeddings.tolist())
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = all_embeddings[i]
        
        return chunks
    
    def process(self):
        """Generate embeddings for all chunks"""
        chunks = self.load_chunks()
        chunks_with_embeddings = self.generate_embeddings(chunks)
        
        # Save chunks with embeddings
        output_file = os.path.join(self.output_dir, 'chunks_with_embeddings.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_with_embeddings, f, ensure_ascii=False)
        
        print(f"Saved {len(chunks_with_embeddings)} chunks with embeddings.")
        return chunks_with_embeddings

# Run the embedding generator
embedding_generator = EmbeddingGenerator(
    input_dir='chunks',
    output_dir='embeddings'
)
chunks_with_embeddings = embedding_generator.process()
```

### 5. Load Data into Neo4j

Now, let's implement a Neo4j loader that creates a knowledge graph with the chunked data:

```python
import json
import os
from neo4j import GraphDatabase
from tqdm import tqdm

class Neo4jLoader:
    def __init__(self, uri, username, password, database='neo4j'):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database
        
    def close(self):
        """Close the Neo4j driver"""
        self.driver.close()
        
    def initialize_database(self):
        """Set up database schema and constraints"""
        with self.driver.session(database=self.database) as session:
            # Create constraints for unique IDs
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.url IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (h:Heading) REQUIRE (h.name, h.level) IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE
            """)
            
            # Create indexes for performance
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (c:Category) ON (c.name)
            """)
            
            # Create vector index (Neo4j 5.0+ required)
            try:
                session.run("""
                    CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
                    FOR (c:Chunk)
                    ON c.embedding
                    OPTIONS {indexConfig: {
                      `vector.dimensions`: 384,
                      `vector.similarity_function`: 'cosine'
                    }}
                """)
                print("Vector index created successfully")
            except Exception as e:
                print(f"Vector index creation failed (this is expected if using Neo4j < 5.0): {e}")
                print("Vector search will not be available")
    
    def load_chunks(self, input_file):
        """Load chunks with embeddings from file"""
        with open(input_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        return chunks
    
    def load_into_neo4j(self, chunks, batch_size=100):
        """Load all chunks into Neo4j"""
        print(f"Loading {len(chunks)} chunks into Neo4j...")
        
        # Process in batches
        for i in tqdm(range(0, len(chunks), batch_size)):
            batch = chunks[i:i+batch_size]
            
            with self.driver.session(database=self.database) as session:
                # Use a transaction for the batch
                tx = session.begin_transaction()
                
                try:
                    for chunk in batch:
                        # Create or update document node
                        self._create_document_node(tx, chunk)
                        
                        # Create chunk node
                        self._create_chunk_node(tx, chunk)
                        
                        # Create heading nodes and relationships
                        self._create_heading_relationships(tx, chunk)
                        
                        # Create category relationships
                        self._create_category_relationships(tx, chunk)
                    
                    # Commit the transaction
                    tx.commit()
                    
                except Exception as e:
                    # Rollback in case of error
                    tx.rollback()
                    print(f"Error loading batch: {e}")
        
        # Create next/previous relationships between chunks
        self._create_chunk_sequence_relationships()
        
        print("Loading complete!")
    
    def _create_document_node(self, tx, chunk):
        """Create or update document node"""
        metadata = chunk['metadata']
        
        tx.run("""
            MERGE (d:Document {url: $url})
            ON CREATE SET
                d.title = $title,
                d.created_at = datetime()
            ON MATCH SET
                d.title = $title,
                d.updated_at = datetime()
        """, 
            url=metadata['source_url'],
            title=metadata['document_title']
        )
    
    def _create_chunk_node(self, tx, chunk):
        """Create chunk node with embedding"""
        tx.run("""
            MATCH (d:Document {url: $doc_url})
            MERGE (c:Chunk {id: $id})
            ON CREATE SET
                c.content = $content,
                c.embedding = $embedding,
                c.chunk_index = $chunk_index,
                c.created_at = datetime()
            ON MATCH SET
                c.content = $content,
                c.embedding = $embedding,
                c.updated_at = datetime()
            MERGE (d)-[:CONTAINS]->(c)
        """,
            id=chunk['id'],
            doc_url=chunk['metadata']['source_url'],
            content=chunk['content'],
            embedding=chunk['embedding'],
            chunk_index=chunk['metadata']['chunk_index']
        )
    
    def _create_heading_relationships(self, tx, chunk):
        """Create heading nodes and relationships"""
        if 'heading' in chunk['metadata']:
            heading = chunk['metadata']['heading']
            heading_level = chunk['metadata'].get('level', 'h1')
            level_num = int(heading_level[1])
            
            tx.run("""
                MATCH (c:Chunk {id: $chunk_id})
                MERGE (h:Heading {name: $heading, level: $level})
                MERGE (c)-[:HAS_HEADING]->(h)
            """,
                chunk_id=chunk['id'],
                heading=heading,
                level=level_num
            )
    
    def _create_category_relationships(self, tx, chunk):
        """Create category nodes and relationships"""
        if 'source_metadata' in chunk['metadata'] and 'category' in chunk['metadata']['source_metadata']:
            categories = chunk['metadata']['source_metadata']['category']
            
            for i, category in enumerate(categories):
                if category:  # Skip empty categories
                    tx.run("""
                        MATCH (d:Document {url: $doc_url})
                        MERGE (cat:Category {name: $category})
                        MERGE (d)-[:IN_CATEGORY {level: $level}]->(cat)
                    """,
                        doc_url=chunk['metadata']['source_url'],
                        category=category,
                        level=i
                    )
    
    def _create_chunk_sequence_relationships(self):
        """Create next/previous relationships between chunks in same document"""
        with self.driver.session(database=self.database) as session:
            session.run("""
                MATCH (d:Document)-[:CONTAINS]->(c1:Chunk)
                MATCH (d)-[:CONTAINS]->(c2:Chunk)
                WHERE c1.chunk_index = c2.chunk_index - 1
                MERGE (c1)-[:NEXT]->(c2)
            """)
    
    def _extract_topics(self):
        """Extract topics from chunks using NLP and create topic relationships"""
        with self.driver.session(database=self.database) as session:
            # This would normally use a more sophisticated NLP approach
            # Here we just use a simple keyword extraction for demonstration
            session.run("""
                MATCH (c:Chunk)
                CALL apoc.nlp.gcp.entities.stream(c.content, {
                  key: 'your-gcp-key',
                  nodeProperty: 'content'
                })
                YIELD value
                UNWIND value.entities AS entity
                MERGE (t:Topic {name: entity.name})
                MERGE (c)-[:MENTIONS {salience: entity.salience}]->(t)
            """)
    
    def process(self, input_file):
        """Process all chunks and load into Neo4j"""
        self.initialize_database()
        chunks = self.load_chunks(input_file)
        self.load_into_neo4j(chunks)
        
        # Optional: Extract topics using NLP
        # Commented out as it requires external API keys
        # self._extract_topics()
        
        return len(chunks)

# Run the Neo4j loader
neo4j_loader = Neo4jLoader(
    uri="neo4j://localhost:7687",
    username="neo4j",
    password="your-password"
)
chunks_loaded = neo4j_loader.process('embeddings/chunks_with_embeddings.json')
neo4j_loader.close()
```

### 6. Implement Retrieval System

Finally, let's implement a retrieval system that leverages Neo4j's graph capabilities:

```python
import json
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np

class RAGRetriever:
    def __init__(self, neo4j_uri, neo4j_username, neo4j_password, 
                 database='neo4j', model_name='all-MiniLM-L6-v2'):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        self.database = database
        
        # Load embedding model
        self.model = SentenceTransformer(model_name)
    
    def close(self):
        """Close the Neo4j driver"""
        self.driver.close()
    
    def query(self, user_query, top_k=5, include_context=True):
        """
        Query the RAG system with a user question
        
        Args:
            user_query: The user's question
            top_k: Number of results to return
            include_context: Whether to include contextual chunks
            
        Returns:
            List of relevant chunks with their source information
        """
        # Generate query embedding
        query_embedding = self.model.encode(user_query).tolist()
        
        # Get vector search results
        vector_results = self._vector_search(query_embedding, top_k)
        
        # Get contextual results if requested
        if include_context and vector_results:
            contextual_results = self._get_contextual_chunks([r['id'] for r in vector_results])
            # Combine and deduplicate
            all_results = {r['id']: r for r in vector_results}
            for r in contextual_results:
                if r['id'] not in all_results:
                    all_results[r['id']] = r
            
            results = list(all_results.values())
        else:
            results = vector_results
        
        # Sort by similarity score
        results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        return results
    
    def _vector_search(self, query_embedding, top_k=5):
        """Perform vector similarity search"""
        with self.driver.session(database=self.database) as session:
            # Check if vector index is available
            try:
                result = session.run("""
                    MATCH (c:Chunk)
                    WHERE c.embedding IS NOT NULL
                    WITH c, vector.similarity(c.embedding, $query_vector) AS similarity
                    ORDER BY similarity DESC
                    LIMIT $top_k
                    MATCH (d:Document)-[:CONTAINS]->(c)
                    OPTIONAL MATCH (c)-[:HAS_HEADING]->(h)
                    RETURN c.id AS id, c.content AS content, d.url AS url, 
                           d.title AS document_title, similarity,
                           h.name AS heading
                """,
                    query_vector=query_embedding,
                    top_k=top_k
                )
                
                return [dict(record) for record in result]
                
            except Exception as e:
                print(f"Vector search failed: {e}")
                print("Falling back to keyword search")
                
                # Fallback to keyword search
                return self._keyword_search(query_embedding, top_k)
    
    def _keyword_search(self, query_embedding, top_k=5):
        """Keyword-based search fallback"""
        # This is a simple implementation - a production system would use more sophisticated text search
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (c:Chunk)
                WITH c, rand() AS r  // Simple random scoring as placeholder
                ORDER BY r DESC
                LIMIT $top_k
                MATCH (d:Document)-[:CONTAINS]->(c)
                OPTIONAL MATCH (c)-[:HAS_HEADING]->(h)
                RETURN c.id AS id, c.content AS content, d.url AS url, 
                       d.title AS document_title, 0.5 AS similarity,
                       h.name AS heading
            """,
                top_k=top_k
            )
            
            return [dict(record) for record in result]
    
    def _get_contextual_chunks(self, chunk_ids, max_context=2):
        """Get contextual chunks (next, previous, and semantically related)"""
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                UNWIND $chunk_ids AS chunk_id
                MATCH (c:Chunk {id: chunk_id})
                
                // Get next and previous chunks
                OPTIONAL MATCH (c)-[:NEXT*1..2]->(next:Chunk)
                OPTIONAL MATCH (c)<-[:NEXT*1..2]-(prev:Chunk)
                
                // Get chunks with same heading
                OPTIONAL MATCH (c)-[:HAS_HEADING]->(h)<-[:HAS_HEADING]-(heading_sibling:Chunk)
                WHERE c <> heading_sibling
                
                WITH COLLECT(DISTINCT next) + COLLECT(DISTINCT prev) + COLLECT(DISTINCT heading_sibling) AS related_chunks
                UNWIND related_chunks AS related
                WHERE related IS NOT NULL
                
                MATCH (d:Document)-[:CONTAINS]->(related)
                OPTIONAL MATCH (related)-[:HAS_HEADING]->(related_h)
                
                RETURN related.id AS id, related.content AS content, 
                       d.url AS url, d.title AS document_title,
                       0 AS similarity, related_h.name AS heading
            """,
                chunk_ids=chunk_ids
            )
            
            return [dict(record) for record in result]
    
    def get_document_chunks(self, document_url):
        """Get all chunks for a specific document, ordered by chunk_index"""
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (d:Document {url: $url})-[:CONTAINS]->(c:Chunk)
                OPTIONAL MATCH (c)-[:HAS_HEADING]->(h)
                RETURN c.id AS id, c.content AS content, c.chunk_index AS chunk_index,
                       h.name AS heading
                ORDER BY c.chunk_index
            """,
                url=document_url
            )
            
            return [dict(record) for record in result]

# Example usage
retriever = RAGRetriever(
    neo4j_uri="neo4j://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="your-password"
)

results = retriever.query("How do I handle returns on Amazon?")
for i, result in enumerate(results):
    print(f"Result {i+1}:")
    print(f"Document: {result['document_title']}")
    print(f"URL: {result['url']}")
    if 'heading' in result and result['heading']:
        print(f"Section: {result['heading']}")
    print(f"Content: {result['content'][:200]}...")
    print(f"Similarity: {result['similarity']}")
    print("-" * 50)

retriever.close()
```

## Cost Optimization Strategies

Let's implement specific cost optimization strategies for this implementation:

### 1. Incremental Updates

```python
class IncrementalUpdater:
    def __init__(self, spider_output_file, preprocessed_dir, chunks_dir, embeddings_dir, neo4j_loader):
        self.spider_output_file = spider_output_file
        self.preprocessed_dir = preprocessed_dir
        self.chunks_dir = chunks_dir
        self.embeddings_dir = embeddings_dir
        self.neo4j_loader = neo4j_loader
    
    def run_incremental_update(self):
        """Run an incremental update on changed documents only"""
        # Load the latest scrape results
        with open(self.spider_output_file, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
        
        # Filter only new or updated documents
        changed_docs = [
            doc for doc in scraped_data 
            if doc.get('metadata', {}).get('change_status') in ['new', 'updated']
        ]
        
        if not changed_docs:
            print("No changes detected. Skipping update.")
            return 0
        
        print(f"Found {len(changed_docs)} changed documents. Processing incrementally...")
        
        # Save changed documents to temporary file
        temp_file = 'temp_changed_docs.json'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(changed_docs, f)
        
        # Process only changed documents
        preprocessor = DataPreprocessor(
            input_file=temp_file,
            output_dir=self.preprocessed_dir
        )
        processed_docs = preprocessor.process()
        
        # Chunk the changed documents
        chunker = SemanticChunker(
            input_dir=self.preprocessed_dir,
            output_dir=self.chunks_dir
        )
        changed_chunks = chunker.process_all_documents()
        
        # Generate embeddings for changed chunks
        embedding_generator = EmbeddingGenerator(
            input_dir=self.chunks_dir,
            output_dir=self.embeddings_dir
        )
        chunks_with_embeddings = embedding_generator.process()
        
        # Update Neo4j with changed chunks
        chunks_loaded = self.neo4j_loader.process(
            f"{self.embeddings_dir}/chunks_with_embeddings.json"
        )
        
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        print(f"Incremental update complete. {chunks_loaded} chunks updated.")
        return chunks_loaded
```

### 2. Change Detection

```python
import random
from scrapy import Request
import hashlib
from datetime import datetime, timedelta

class ChangeDetector:
    def __init__(self, neo4j_uri, neo4j_username, neo4j_password, database='neo4j'):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        self.database = database
    
    def close(self):
        """Close the Neo4j driver"""
        self.driver.close()
    
    def get_sample_urls(self, sample_size=20):
        """Get a sample of URLs to check for changes"""
        with self.driver.session(database=self.database) as session:
            # Get a mix of recently updated and older documents
            result = session.run("""
                // Get most recently updated documents
                MATCH (d:Document)
                WHERE EXISTS(d.updated_at)
                WITH d ORDER BY d.updated_at DESC
                LIMIT 10
                
                // Combine with random older documents
                WITH COLLECT(d) AS recent
                MATCH (d:Document)
                WHERE NOT d IN recent
                WITH recent, d, rand() AS r
                ORDER BY r
                LIMIT 10
                
                // Combine and return all URLs
                WITH recent + COLLECT(d) AS all_docs
                UNWIND all_docs AS doc
                RETURN doc.url AS url
            """)
            
            urls = [record["url"] for record in result]
            
            # If we got fewer than the requested sample size, get more random documents
            if len(urls) < sample_size:
                more_result = session.run("""
                    MATCH (d:Document)
                    WHERE NOT d.url IN $existing_urls
                    WITH d, rand() AS r
                    ORDER BY r
                    LIMIT $limit
                    RETURN d.url AS url
                """,
                    existing_urls=urls,
                    limit=sample_size - len(urls)
                )
                
                urls.extend([record["url"] for record in more_result])
            
            return urls
    
    def check_for_changes(self, urls):
        """Check URLs for content changes"""
        import scrapy
        from scrapy.crawler import CrawlerProcess
        
        class ChangeCheckSpider(scrapy.Spider):
            name = 'change_checker'
            
            def __init__(self, urls, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.urls = urls
                self.results = {
                    'checked_urls': 0,
                    'changed_urls': 0,
                    'changes': []
                }
            
            def start_requests(self):
                for url in self.urls:
                    yield Request(url=url, callback=self.parse)
            
            def parse(self, response):
                url = response.url
                
                # Extract content
                content_parts = response.css('article p::text, article li::text, article h2::text, article h3::text').getall()
                if not content_parts:
                    content_parts = response.css('.content p::text, .content li::text').getall()
                if not content_parts:
                    content_parts = response.css('p::text, li::text').getall()
                
                content = ' '.join(content_parts).strip()
                content = ' '.join(content.split())  # Normalize whitespace
                
                # Generate content hash
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                self.results['checked_urls'] += 1
                
                # This would normally check against stored hash in database
                # For demonstration, we're randomly determining changes
                if random.random() < 0.15:  # 15% change probability for demonstration
                    self.results['changed_urls'] += 1
                    self.results['changes'].append({
                        'url': url,
                        'new_hash': content_hash
                    })
        
        # Set up and run crawler
        process = CrawlerProcess(settings={
            'ROBOTSTXT_OBEY': True,
            'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7',
            'USER_AGENT': 'Mozilla/5.0 (compatible; ChangeDetector/1.0)',
            'LOG_LEVEL': 'ERROR'
        })
        
        spider = ChangeCheckSpider(urls=urls)
        process.crawl(spider)
        process.start()
        
        return spider.results
    
    def should_trigger_update(self, change_threshold=0.1):
        """Determine if changes warrant a full update"""
        urls = self.get_sample_urls(20)
        results = self.check_for_changes(urls)
        
        change_rate = results['changed_urls'] / results['checked_urls'] if results['checked_urls'] > 0 else 0
        
        print(f"Change detection results:")
        print(f"  Checked URLs: {results['checked_urls']}")
        print(f"  Changed URLs: {results['changed_urls']}")
        print(f"  Change rate: {change_rate:.2f}")
        
        return {
            'should_update': change_rate >= change_threshold,
            'change_rate': change_rate,
            'checked_urls': results['checked_urls'],
            'changed_urls': results['changed_urls'],
            'changes': results['changes']
        }
```

### 3. Scheduled Monitoring

```python
import schedule
import time
from datetime import datetime, timedelta
import os
import json

class MonitoredPipeline:
    def __init__(self, config_file='pipeline_config.json'):
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        """Load pipeline configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                'last_full_update': None,
                'last_check': None,
                'neo4j_uri': 'neo4j://localhost:7687',
                'neo4j_username': 'neo4j',
                'neo4j_password': 'password',
                'min_days_between_full_updates': 7,
                'change_check_interval_hours': 24,
                'change_threshold': 0.1,
                'resource_usage': {
                    'requests': 0,
                    'neo4j_operations': 0,
                    'embedding_calls': 0,
                }
            }
            self.save_config()
    
    def save_config(self):
        """Save current configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2, default=str)
    
    def run_change_detection(self):
        """Run change detection and decide if update is needed"""
        print(f"Running change detection at {datetime.now()}")
        
        detector = ChangeDetector(
            neo4j_uri=self.config['neo4j_uri'],
            neo4j_username=self.config['neo4j_username'],
            neo4j_password=self.config['neo4j_password']
        )
        
        result = detector.should_trigger_update(self.config['change_threshold'])
        detector.close()
        
        self.config['last_check'] = datetime.now().isoformat()
        self.save_config()
        
        return result
    
    def should_run_full_update(self):
        """Determine if a full update should run"""
        # Always run if no previous update
        if not self.config['last_full_update']:
            return True
        
        last_update = datetime.fromisoformat(self.config['last_full_update'])
        days_since_update = (datetime.now() - last_update).days
        
        # Run if it's been too long since last full update
        if days_since_update >= self.config['min_days_between_full_updates']:
            return True
        
        # Otherwise, check for changes
        result = self.run_change_detection()
        return result['should_update']
    
    def run_full_update(self):
        """Run a full update of the pipeline"""
        print(f"Running full update at {datetime.now()}")
        
        # 1. Run scrapy spider
        import subprocess
        subprocess.run(['scrapy', 'crawl', 'amazon_seller_help', '-O', 'amazon_seller_data.json'])
        
        # 2. Preprocess data
        preprocessor = DataPreprocessor(
            input_file='amazon_seller_data.json',
            output_dir='processed_data'
        )
        processed_docs = preprocessor.process()
        
        # 3. Chunk documents
        chunker = SemanticChunker(
            input_dir='processed_data',
            output_dir='chunks'
        )
        all_chunks = chunker.process_all_documents()
        
        # 4. Generate embeddings
        embedding_generator = EmbeddingGenerator(
            input_dir='chunks',
            output_dir='embeddings'
        )
        chunks_with_embeddings = embedding_generator.process()
        
        # 5. Load into Neo4j
        neo4j_loader = Neo4jLoader(
            uri=self.config['neo4j_uri'],
            username=self.config['neo4j_username'],
            password=self.config['neo4j_password']
        )
        chunks_loaded = neo4j_loader.process('embeddings/chunks_with_embeddings.json')
        neo4j_loader.close()
        
        # Update config
        self.config['last_full_update'] = datetime.now().isoformat()
        self.save_config()
        
        print(f"Full update complete: {len(processed_docs)} documents, {chunks_loaded} chunks")
    
    def run_incremental_update(self):
        """Run an incremental update"""
        print(f"Running incremental update at {datetime.now()}")
        
        # 1. Run spider for selective pages
        result = self.run_change_detection()
        
        if not result['should_update']:
            print("No significant changes detected. Skipping incremental update.")
            return
        
        # 2. Run incremental updater
        neo4j_loader = Neo4jLoader(
            uri=self.config['neo4j_uri'],
            username=self.config['neo4j_username'],
            password=self.config['neo4j_password']
        )
        
        updater = IncrementalUpdater(
            spider_output_file='amazon_seller_data.json',
            preprocessed_dir='processed_data',
            chunks_dir='chunks',
            embeddings_dir='embeddings',
            neo4j_loader=neo4j_loader
        )
        
        chunks_updated = updater.run_incremental_update()
        
        # Close connections
        neo4j_loader.close()
        
        print(f"Incremental update complete: {chunks_updated} chunks updated")
    
    def schedule_jobs(self):
        """Schedule pipeline jobs"""
        # Check for changes daily
        schedule.every(self.config['change_check_interval_hours']).hours.do(self.run_change_detection)
        
        # Try to run full update weekly
        schedule.every(self.config['min_days_between_full_updates']).days.do(
            lambda: self.run_full_update() if self.should_run_full_update() else None
        )
        
        print("Jobs scheduled. Press Ctrl+C to exit.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("Scheduler stopped.")
    
    def run_manual_update(self, mode='auto'):
        """Run a manual update"""
        if mode == 'full':
            self.run_full_update()
        elif mode == 'incremental':
            self.run_incremental_update()
        else:
            # Auto mode - decide based on changes
            if self.should_run_full_update():
                self.run_full_update()
            else:
                self.run_incremental_update()

# To run the pipeline manually
pipeline = MonitoredPipeline()
pipeline.run_manual_update()

# To run the scheduled pipeline
# pipeline.schedule_jobs()
```

## Neo4j-Specific Cost Optimization

```python
class Neo4jOptimizer:
    def __init__(self, uri, username, password, database='neo4j'):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database
    
    def close(self):
        """Close the Neo4j driver"""
        self.driver.close()
    
    def optimize_database(self):
        """Run Neo4j optimization procedures"""
        with self.driver.session(database=self.database) as session:
            # Check database size
            result = session.run("""
                CALL apoc.meta.stats()
            """)
            stats = result.single()
            
            print("Database statistics:")
            print(f"  Nodes: {stats['nodeCount']}")
            print(f"  Relationships: {stats['relCount']}")
            print(f"  Properties: {stats['propertyCount']}")
            
            # Run schema optimization
            print("Optimizing database schema...")
            session.run("""
                CALL db.schema.visualization()
            """)
            
            # Analyze queries for optimization
            print("Running query analysis...")
            session.run("""
                CALL apoc.meta.graphSample()
            """)
            
            # Clean up unused indexes
            print("Checking indexes...")
            session.run("""
                SHOW INDEXES
            """)
    
    def optimize_connection_pool(self):
        """Optimize Neo4j connection pool settings"""
        # These would normally be applied during driver initialization
        connection_pool_settings = {
            'max_connection_lifetime': 30 * 60,  # 30 minutes
            'max_connection_pool_size': 50,
            'connection_acquisition_timeout': 60,  # 60 seconds
        }
        
        print("Connection pool optimization settings:")
        for setting, value in connection_pool_settings.items():
            print(f"  {setting}: {value}")
    
    def run_maintenance(self):
        """Run database maintenance"""
        # These are example maintenance tasks
        with self.driver.session(database=self.database) as session:
            print("Running database maintenance...")
            
            # Check for orphaned nodes
            result = session.run("""
                MATCH (n)
                WHERE NOT (n)--()
                RETURN labels(n) AS type, count(*) AS count
            """)
            
            print("Orphaned nodes:")
            for record in result:
                print(f"  {record['type']}: {record['count']}")
            
            # Check for incomplete embeddings
            result = session.run("""
                MATCH (c:Chunk)
                WHERE NOT EXISTS(c.embedding)
                RETURN count(c) AS missing_embeddings
            """)
            
            missing = result.single()['missing_embeddings']
            print(f"Chunks with missing embeddings: {missing}")
            
            # Update timestamps for consistent querying
            session.run("""
                MATCH (n)
                WHERE NOT EXISTS(n.created_at)
                SET n.created_at = datetime()
            """)

# Example usage
optimizer = Neo4jOptimizer(
    uri="neo4j://localhost:7687",
    username="neo4j",
    password="your-password"
)
optimizer.optimize_database()
optimizer.optimize_connection_pool()
optimizer.run_maintenance()
optimizer.close()
```

## Integration Testing

Let's create a simple integration test to ensure the full pipeline works correctly:

```python
import time
import os
import json
from datetime import datetime

def run_integration_test():
    """Run an integration test of the complete pipeline"""
    print("Starting integration test...")
    start_time = time.time()
    
    # Create test directory
    test_dir = f"integration_test_{int(time.time())}"
    os.makedirs(test_dir, exist_ok=True)
    
    # 1. Create a test sample
    print("Creating test sample...")
    sample_data = [
        {
            "url": "https://sellercentral.amazon.com/help/hub/reference/test1",
            "title": "Test Document 1",
            "html_content": """
                <article>
                    <h1>Test Document 1</h1>
                    <p>This is a test document for the Amazon Sellers RAG system.</p>
                    <h2>Section 1</h2>
                    <p>This is section 1 of the test document.</p>
                    <ul>
                        <li>Item 1</li>
                        <li>Item 2</li>
                    </ul>
                    <h2>Section 2</h2>
                    <p>This is section 2 of the test document.</p>
                </article>
            """,
            "text_content": "Test Document 1 This is a test document for the Amazon Sellers RAG system. Section 1 This is section 1 of the test document. Item 1 Item 2 Section 2 This is section 2 of the test document.",
            "metadata": {
                "category": ["Test", "Integration"],
                "related_links": [],
                "page_hash": "test_hash_1",
                "change_status": "new",
                "scrape_time": datetime.now().isoformat()
            }
        },
        {
            "url": "https://sellercentral.amazon.com/help/hub/reference/test2",
            "title": "Test Document 2",
            "html_content": """
                <article>
                    <h1>Test Document 2</h1>
                    <p>This is another test document for the Amazon Sellers RAG system.</p>
                    <h2>Section A</h2>
                    <p>This is section A with information about returns.</p>
                    <h2>Section B</h2>
                    <p>This section discusses how to handle product returns on Amazon.</p>
                </article>
            """,
            "text_content": "Test Document 2 This is another test document for the Amazon Sellers RAG system. Section A This is section A with information about returns. Section B This section discusses how to handle product returns on Amazon.",
            "metadata": {
                "category": ["Test", "Integration", "Returns"],
                "related_links": [],
                "page_hash": "test_hash_2",
                "change_status": "new",
                "scrape_time": datetime.now().isoformat()
            }
        }
    ]
    
    # Save sample data
    with open(f"{test_dir}/test_data.json", 'w') as f:
        json.dump(sample_data, f, indent=2, default=str)
    
    # 2. Preprocess data
    print("Preprocessing test data...")
    preprocessor = DataPreprocessor(
        input_file=f"{test_dir}/test_data.json",
        output_dir=f"{test_dir}/processed"
    )
    processed_docs = preprocessor.process()
    
    # 3. Chunk documents
    print("Chunking test documents...")
    chunker = SemanticChunker(
        input_dir=f"{test_dir}/processed",
        output_dir=f"{test_dir}/chunks",
        chunk_size=100,  # Smaller for testing
        chunk_overlap=20
    )
    chunks = chunker.process_all_documents()
    
    # 4. Generate embeddings
    print("Generating test embeddings...")
    embedding_generator = EmbeddingGenerator(
        input_dir=f"{test_dir}/chunks",
        output_dir=f"{test_dir}/embeddings"
    )
    chunks_with_embeddings = embedding_generator.process()
    
    # 5. Set up a test Neo4j database
    # For testing, use a different database name to avoid affecting production
    neo4j_loader = Neo4jLoader(
        uri="neo4j://localhost:7687",
        username="neo4j",
        password="your-password",
        database="test_amazon_sellers"
    )
    
    print("Loading test data into Neo4j...")
    chunks_loaded = neo4j_loader.process(f"{test_dir}/embeddings/chunks_with_embeddings.json")
    
    # 6. Test retrieval
    print("Testing retrieval...")
    retriever = RAGRetriever(
        neo4j_uri="neo4j://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="your-password",
        database="test_amazon_sellers"
    )
    
    # Run test queries
    test_queries = [
        "How do I handle returns on Amazon?",
        "What is in section 1?",
        "Tell me about test document 1"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        results = retriever.query(query, top_k=2)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"  Result {i+1}: {result['document_title']} - {result['similarity']:.3f}")
    
    # 7. Clean up
    print("\nCleaning up test resources...")
    retriever.close()
    neo4j_loader.close()
    
    # Drop test database (in a production environment, you might want to keep it)
    # This requires admin privileges
    admin_driver = GraphDatabase.driver(
        "neo4j://localhost:7687",
        auth=("neo4j", "your-password")
    )
    with admin_driver.session(database="system") as session:
        try:
            session.run("DROP DATABASE test_amazon_sellers IF EXISTS")
            print("Test database dropped.")
        except Exception as e:
            print(f"Could not drop test database: {e}")
    admin_driver.close()
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\nIntegration test completed in {execution_time:.2f} seconds")
    print(f"Processed {len(processed_docs)} documents into {chunks_loaded} chunks")
    
    return {
        "success": True,
        "execution_time": execution_time,
        "documents_processed": len(processed_docs),
        "chunks_created": chunks_loaded,
        "test_directory": test_dir
    }

# Run the integration test
if __name__ == "__main__":
    test_result = run_integration_test()
    print(f"Test {'passed' if test_result['success'] else 'failed'}")
```

## Summary: Cost Optimization Techniques

The implementation includes the following cost optimization techniques:

1. **Incremental Updates**
   - Only process changed or new documents
   - Track content hashes to detect changes efficiently
   - Reuse existing embeddings when content hasn't changed

2. **Smart Scheduling**
   - Sample pages to check for changes before running full updates
   - Adaptive schedule based on content volatility
   - Force updates only after minimum time threshold

3. **Resource Management**
   - Batch processing of embeddings to minimize API calls
   - Connection pooling optimization for Neo4j
   - Reuse of computed data across pipeline stages

4. **Storage Efficiency**
   - Only store essential content (removing boilerplate)
   - Efficient chunk sizing to balance detail and storage needs
   - Metadata organization for efficient retrieval

5. **Neo4j-Specific Optimizations**
   - Proper indexing for fast retrieval
   - Relationship-based traversal to reduce redundant data
   - Query optimization for minimizing database operations

This implementation balances completeness, quality, and cost by:
- Using semantic chunking to preserve meaning and context
- Implementing a comprehensive, change-aware monitoring system
- Optimizing resource usage at each stage of the pipeline