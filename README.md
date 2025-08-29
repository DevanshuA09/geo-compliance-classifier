# Geo-Compliance Classifier 🏛️

A comprehensive machine learning system for classifying geo-specific compliance requirements for social media platforms, featuring dual agents for document preprocessing and regulation retrieval.

## 🎯 **System Overview**

This project combines two powerful AI agents:

1. **📄 Artifact Preprocessor Agent**: Normalizes PRD/TRD documents, extracts structured fields, and expands TikTok codenames
2. **🔍 Regulation Retriever Agent**: Provides sub-second legal snippet retrieval from four key regulations using hybrid search

## 🚀 **Quick Start - Regulation Retriever**

### Install Dependencies
```bash
pip install -r requirements_retriever.txt
```

### Build Index & Start Service
```bash
# Build vector index from legal documents
python -c "
from index.build_index import VectorIndexBuilder
builder = VectorIndexBuilder()
stats = builder.build_index()
print(f'Built index: {stats.total_chunks} chunks, {stats.build_time_seconds:.2f}s')
"

# Start FastAPI server
uvicorn retriever.service:app --host 0.0.0.0 --port 8000
```

### Use Python SDK
```python
from sdk.client import RegulationClient

client = RegulationClient()
results = client.retrieve(
    query="parental consent for 14-15 year olds in California", 
    laws=["CA_SB976"],
    top_k=3
)

for result in results:
    print(f"📄 {result.law_name}")
    print(f"📍 {result.section_label}")  
    print(f"💬 {result.snippet}")
```

### CLI Interface
```bash
python -m retriever.cli "age verification requirements" --laws FL_HB3 --k 3
```

## 📊 **Legal Sources**

| Law ID | Full Name | Jurisdiction | Key Focus |
|--------|-----------|--------------|-----------|
| `EUDSA` | EU Digital Services Act (DSA) | EU | Systemic risk, transparency, minors |
| `CA_SB976` | California Social Media Addiction Act | US-CA | Default privacy, algorithms, minors |
| `FL_HB3` | Florida Online Protections for Minors | US-FL | Age verification, parental consent |
| `US_2258A` | 18 U.S.C. §2258A NCMEC Reporting | US | Child exploitation reporting |

## 🎯 **Regulation Retriever Features**

- **🚀 Sub-second Performance**: P95 < 1000ms with LRU caching
- **🔍 Hybrid Search**: BM25 sparse + dense vector fusion
- **🎯 Smart Chunking**: Section-aware segmentation with metadata
- **⚡ FastAPI Service**: Production-ready REST API  
- **🐍 Python SDK**: Developer-friendly client
- **📊 Evaluation Suite**: 15 canned queries with Hit@K metrics

## 🚀 **Quick Start - Artifact Preprocessor**

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Process features CSV with terminology expansion
python -m artifact_preprocessor.cli \
  --features feature_sample_data.csv \
  --terms terminology.csv \
  --out ./out

# Process documents directory
python -m artifact_preprocessor.cli \
  --docs ./docs \
  --terms terminology.csv \
  --out ./out

# Process both features and documents
python -m artifact_preprocessor.cli \
  --features feature_sample_data.csv \
  --terms terminology.csv \
  --docs ./docs \
  --out ./out
```

## Input Formats

### Terminology CSV
Required columns: `term`, `explanation`
```csv
term,explanation
ASL,Age-sensitive logic
PF,Personalized feed
GH,Geo-handler; a module responsible for routing features based on user region
```

### Features CSV
Required columns: `feature_name`, `feature_description`
```csv
feature_name,feature_description
Curfew login blocker,To comply with the Utah Social Media Regulation Act...
```

### Document Files
Supported formats:
- **PDF**: Using PyPDF2 with pdfminer.six fallback
- **DOCX**: Using python-docx (paragraphs and tables)
- **Markdown**: Using markdown library with plain text fallback
- **HTML**: Using BeautifulSoup4 with regex fallback  
- **TXT**: Direct UTF-8 reading with encoding detection

## Output Files

The processor generates three main outputs in the specified directory:

### 1. `preprocessed.jsonl`
JSON Lines format with one feature record per line:
```json
{
  "feature_id": "csv_feature_0001",
  "doc_type": "csv",
  "feature_title": "Curfew login blocker with ASL and GH for Utah minors",
  "feature_description": "To comply with the Utah Social Media...",
  "text_original_hash": "abc123...",
  "text_expanded_hash": "def456...",
  "codename_hits_json": [
    {
      "term": "ASL",
      "expansion": "Age-sensitive logic", 
      "count": 2,
      "spans": [[45, 48], [112, 115]]
    }
  ],
  "parse_warnings": "",
  "source_path": "features.csv"
}
```

### 2. `preprocessed.csv`
Same data in CSV format for analysis tools.

### 3. `expansion_report.csv`
Codename expansion summary:
```csv
feature_id,term,expansion,count
csv_feature_0001,ASL,Age-sensitive logic,2
csv_feature_0001,GH,Geo-handler; a module responsible for routing features based on user region,1
```

### 4. `report.md`
Processing report with statistics, field extraction rates, warnings, and success metrics.

## Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Files   │───▶│   File Parsers   │───▶│   Normalize     │
│                 │    │                  │    │                 │
│ • CSV Features  │    │ • PDF Parser     │    │ • Strip boiler  │
│ • Documents     │    │ • DOCX Parser    │    │ • Clean bullets │
│ • Terminology   │    │ • MD/HTML Parser │    │ • Fix headings  │
└─────────────────┘    │ • TXT Parser     │    └─────────────────┘
                       └──────────────────┘             │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Output Files  │◀───│  Generate Outputs│◀───│ Extract & Expand│
│                 │    │                  │    │                 │
│ • preprocessed  │    │ • JSONL Writer   │    │ • Field Extract │
│ • expansion_rpt │    │ • CSV Writer     │    │ • Codename Match│
│ • report.md     │    │ • Report Gen     │    │ • Hash Content  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Extracted Fields

The processor extracts 15+ structured fields using fuzzy header matching:

**Document Metadata:**
- `doc_title`, `version`, `authors`, `date`

**Feature Content:**  
- `feature_title`, `feature_description`

**Structured Sections:**
- `objectives`, `scope`, `user_segments`
- `risk_safety`, `privacy_data`, `age_gating`  
- `geo_regions`, `rollout`, `open_questions`
- `appendix_raw`

## Codename Expansion

Expands TikTok internal codenames with inline annotations:

**Input:**
```
The PF uses ASL to detect minors for GH routing.
```

**Output:**
```  
The PF [Personalized feed] uses ASL [Age-sensitive logic] to detect minors for GH [Geo-handler; a module responsible for routing features based on user region] routing.
```

**Features:**
- Word-boundary matching (avoids partial matches)
- Case-insensitive detection
- Preserves original tokens
- Deterministic expansion order
- Deduplication of repeated terms

## Success Metrics

The processor tracks and reports:

- **Parse Success Rate**: Percentage of documents successfully processed
- **Field Extraction Rate**: Average percentage of fields extracted per document  
- **Expansion Coverage**: Percentage of terminology terms found
- **Warning Count**: Number of recoverable processing issues

**Target**: 100% parse success rate for well-formed inputs.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=artifact_preprocessor

# Format code
black artifact_preprocessor/ tests/

# Lint code  
ruff check artifact_preprocessor/ tests/
```

## Testing

The test suite includes:

- **Unit tests** for each parser type
- **Field extraction tests** with various document structures
- **Codename expansion tests** with edge cases
- **End-to-end tests** with sample documents
- **Success rate validation** with threshold checking

```bash
# Run specific test modules
pytest tests/test_parsers.py
pytest tests/test_extraction.py  
pytest tests/test_expansion.py
pytest tests/test_end_to_end.py
```

## Error Handling

The processor never crashes on malformed inputs:

- **Missing files**: Clear error messages
- **Encoding issues**: Auto-detection with fallback
- **Parse failures**: Logged as warnings, processing continues
- **Empty content**: Handled gracefully with warnings
- **Invalid patterns**: Skipped with debug logging

## Configuration

Logging levels and behavior can be configured:

```bash
# Enable debug logging
python -m artifact_preprocessor.cli --verbose

# Set specific log level
python -m artifact_preprocessor.cli --log-level WARNING
```

## Requirements

- **Python**: 3.10+
- **Core dependencies**: PyPDF2, pdfminer.six, python-docx, beautifulsoup4, markdown, chardet
- **Development**: pytest, black, ruff

## License

MIT License - see LICENSE file for details.
