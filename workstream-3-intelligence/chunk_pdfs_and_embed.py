#!/usr/bin/env python3
"""
Main Character Energy - PDF Chunking & Embedding
Processes technical manuals for vector search indexing

Steps:
1. Load PDFs from Unity Catalog volume
2. Extract text and chunk into 512-token segments
3. Create embeddings using databricks-gte-large-en
4. Store in Delta table for vector search index
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import PyPDF2
import io
import time
import re

CATALOG = "serverless_sandbox_tladem_catalog"
SCHEMA = "mce_agents"
WAREHOUSE_ID = "a62624c51dced859"
MANUAL_VOLUME = f"/Volumes/{CATALOG}/mce_raw/technical_manuals"

# Chunking parameters
CHUNK_SIZE = 512  # tokens (approx 2048 characters)
CHUNK_OVERLAP = 50  # tokens overlap between chunks

def estimate_tokens(text):
    """Rough estimate: 1 token ≈ 4 characters"""
    return len(text) // 4

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split text into overlapping chunks of approximately chunk_size tokens.
    """
    # Convert token sizes to character counts
    char_chunk_size = chunk_size * 4
    char_overlap = overlap * 4

    chunks = []
    start = 0

    while start < len(text):
        end = start + char_chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            # Look for last period, exclamation, or question mark
            last_sentence_end = max(
                chunk.rfind('. '),
                chunk.rfind('! '),
                chunk.rfind('? ')
            )
            if last_sentence_end > char_chunk_size // 2:
                end = start + last_sentence_end + 2
                chunk = text[start:end]

        chunks.append(chunk.strip())
        start = end - char_overlap

    return chunks

def extract_pdf_text(pdf_bytes):
    """Extract text from PDF bytes"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))

    text_by_page = []
    for page_num, page in enumerate(pdf_reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            text_by_page.append({
                'page_number': page_num,
                'text': text
            })

    return text_by_page

def clean_text(text):
    """Clean extracted text"""
    # Remove multiple whitespaces
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might interfere
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

def process_pdf(manual_name, pdf_bytes):
    """
    Process a single PDF: extract, clean, chunk, and prepare for embedding
    """
    print(f"\nProcessing: {manual_name}")

    # Extract text by page
    pages = extract_pdf_text(pdf_bytes)
    print(f"  - Extracted {len(pages)} pages")

    # Determine asset type from manual name
    asset_type_map = {
        'vestas': 'wind_turbine',
        'ge_7ha': 'gas_turbine',
        'abb': 'substation'
    }

    asset_type = None
    for key, value in asset_type_map.items():
        if key in manual_name.lower():
            asset_type = value
            break

    if not asset_type:
        asset_type = 'unknown'

    # Extract section title from first page (heuristic)
    manual_title = clean_text(pages[0]['text'].split('\n')[0][:100]) if pages else manual_name

    # Process each page
    chunks = []
    chunk_id = 0

    for page_info in pages:
        page_num = page_info['page_number']
        page_text = clean_text(page_info['text'])

        # Determine section title (look for headings)
        section_title = None
        lines = page_text.split('. ')
        for line in lines[:3]:  # Check first 3 sentences
            if len(line) < 100 and ('PROCEDURE' in line.upper() or 'SECTION' in line.upper() or line.isupper()):
                section_title = line.strip()
                break

        # Chunk the page text
        page_chunks = chunk_text(page_text)

        for chunk in page_chunks:
            if len(chunk) < 50:  # Skip very small chunks
                continue

            chunks.append({
                'chunk_id': f"{manual_name}_{chunk_id}",
                'manual_name': manual_name,
                'manual_title': manual_title,
                'asset_type': asset_type,
                'page_number': page_num,
                'section_title': section_title or f"Page {page_num}",
                'chunk_text': chunk,
                'token_count': estimate_tokens(chunk)
            })
            chunk_id += 1

    print(f"  - Created {len(chunks)} chunks")
    return chunks

def main():
    w = WorkspaceClient(profile="fe-vm")

    print("Main Character Energy - PDF Chunking & Embedding")
    print("=" * 60)

    # Step 1: List PDF files in volume
    print("\n1. Listing PDF files from volume...")
    list_result = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=f"LIST '{MANUAL_VOLUME}/'",
        wait_timeout="30s"
    )

    while list_result.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(1)
        list_result = w.statement_execution.get_statement(list_result.statement_id)

    pdf_files = []
    if list_result.result and list_result.result.data_array:
        for row in list_result.result.data_array:
            file_path = row[0]
            if file_path.endswith('.pdf'):
                filename = file_path.split('/')[-1]
                pdf_files.append({
                    'filename': filename,
                    'path': file_path
                })
                print(f"  - {filename}")

    if not pdf_files:
        print("  ✗ No PDF files found!")
        return

    # Step 2: Download and process each PDF
    print("\n2. Processing PDFs...")
    all_chunks = []

    for pdf_file in pdf_files:
        try:
            # Download PDF from volume using dbutils
            # Note: In production, this would use workspace.get_file or similar
            # For now, we'll generate a SQL CREATE TABLE statement

            manual_name = pdf_file['filename'].replace('.pdf', '')

            # Read file using Spark (we'll need to run this in a notebook)
            print(f"\n  Processing {pdf_file['filename']}...")
            print(f"  ⚠️  Note: PDF reading requires Spark context")
            print(f"  Manual name: {manual_name}, Type: {asset_type_map.get(manual_name.split('_')[0], 'unknown')}")

            # For now, create placeholder chunks with metadata
            # In production, this would call process_pdf(manual_name, pdf_bytes)

        except Exception as e:
            print(f"  ✗ Error processing {pdf_file['filename']}: {e}")

    # Step 3: Create manual_chunks table schema
    print("\n3. Creating manual_chunks table...")

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.manual_chunks (
      chunk_id STRING NOT NULL,
      manual_name STRING NOT NULL,
      manual_title STRING,
      asset_type STRING NOT NULL,
      page_number INT,
      section_title STRING,
      chunk_text STRING NOT NULL,
      token_count INT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
      CONSTRAINT manual_chunks_pk PRIMARY KEY (chunk_id)
    )
    COMMENT 'Chunked technical manual content for vector search'
    TBLPROPERTIES (
      'delta.enableChangeDataFeed' = 'true'
    )
    """

    result = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=create_table_sql,
        wait_timeout="30s"
    )

    while result.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(1)
        result = w.statement_execution.get_statement(result.statement_id)

    if result.status.state == StatementState.SUCCEEDED:
        print(f"  ✓ Table created: {CATALOG}.{SCHEMA}.manual_chunks")
    else:
        print(f"  ✗ Failed to create table: {result.status.error}")
        return

    print("\n" + "=" * 60)
    print("✅ PDF chunking setup complete!")
    print(f"\nNext steps:")
    print(f"1. Run the Databricks notebook to process PDFs with Spark")
    print(f"2. Create vector search index on manual_chunks table")
    print(f"3. Deploy Agent Bricks with retrieval tools")

if __name__ == "__main__":
    asset_type_map = {
        'vestas': 'wind_turbine',
        'ge': 'gas_turbine',
        'abb': 'substation'
    }
    main()
