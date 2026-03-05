# 🌍 Geo-Compliance Classifier Project - Complete Tools Documentation

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Core AI/ML Models](#core-aiml-models)
3. [RAG (Retrieval-Augmented Generation) System](#rag-retrieval-augmented-generation-system)
4. [Evidence Management System](#evidence-management-system)
5. [Compliance Agents](#compliance-agents)
6. [Data Processing Pipeline](#data-processing-pipeline)
7. [Monitoring & Reporting](#monitoring--reporting)
8. [CLI Tools](#cli-tools)
9. [Utility Tools](#utility-tools)
10. [Integration & API Tools](#integration--api-tools)

---

## 🎯 Project Overview

The Geo-Compliance Classifier is a comprehensive AI-powered compliance framework designed to automatically classify and validate social media features against multi-jurisdictional regulatory requirements. The system integrates multiple AI models, RAG capabilities, and automated compliance workflows to ensure regulatory adherence across EU, US, and global jurisdictions.

**Key Capabilities:**
- Multi-jurisdictional compliance analysis (EU DSA, GDPR, US state laws)
- AI-powered feature classification and risk assessment
- Automated evidence collection and verification
- Active learning for continuous model improvement
- Comprehensive compliance reporting and monitoring

---

## 🤖 Core AI/ML Models

### 1. LLM RAG Model (`src/models/llm_rag_model.py`)

**Purpose:** General-purpose LLM integration with RAG for compliance detection

**Input Structure:**
```python
text: str  # Input text to classify for compliance
```

**Output Structure:**
```python
Tuple[str, float]  # (decision, confidence_score)
# decision: "COMPLIANT" | "NON-COMPLIANT" | "UNCLEAR"
# confidence_score: 0.0-1.0
```

**Key Features:**
- Integrates with OpenAI GPT-4/Claude models
- Uses centralized RAG system for regulatory context
- Fallback prediction mechanism for API failures
- Structured JSON response parsing

**Configuration:**
- Model selection (GPT-4, Claude, etc.)
- API key management
- RAG adapter integration

---

### 2. Legal BERT Model (`src/models/legal_bert_model.py`)

**Purpose:** Specialized BERT model for legal text classification

**Input Structure:**
```python
text: str  # Legal text to classify
```

**Output Structure:**
```python
Tuple[str, float]  # (prediction, confidence)
# prediction: Compliance classification
# confidence: Model confidence score
```

**Key Features:**
- Pre-trained on legal corpora
- Specialized for compliance detection
- High accuracy on legal terminology

---

### 3. Rules-Based Classifier (`src/models/rules_based_classifier.py`)

**Purpose:** Deterministic classification using predefined compliance rules

**Input Structure:**
```python
text: str  # Text to classify
jurisdiction: str  # Target jurisdiction (e.g., "EU", "US-CA")
```

**Output Structure:**
```python
Tuple[str, float]  # (classification, confidence)
# classification: Rule-based decision
# confidence: Rule match confidence
```

**Key Features:**
- Deterministic rule matching
- Jurisdiction-specific rule sets
- High interpretability
- Fast execution

---

## 🔍 RAG (Retrieval-Augmented Generation) System

### 1. RAG Adapter (`src/rag/rag_adapter.py`)

**Purpose:** Unified interface for all agents to access the centralized RAG system

**Input Structure:**
```python
query: str  # Search query text
jurisdiction: Optional[str]  # Optional jurisdiction filter
max_results: int  # Maximum number of results (default: 5)
```

**Output Structure:**
```python
List[Dict[str, Any]]  # List of regulatory context results
# Each result contains:
# - text: str (retrieved text)
# - source: str (document source)
# - relevance_score: float
# - metadata: Dict
```

**Key Features:**
- Unified interface for FAISS and legacy retrieval
- Automatic fallback mechanisms
- Evidence logging integration
- Performance monitoring

---

### 2. Retrieval Service (`retriever/service.py`)

**Purpose:** High-performance regulation retrieval service with caching

**Input Structure:**
```python
query: str  # Search query
laws: Optional[Set[str]]  # Law filter set
top_k: int  # Number of results
max_chars: int  # Maximum characters per result
```

**Output Structure:**
```python
RetrievalResponse:
  query: str
  results: List[SearchResult]
  total_results: int
  retrieval_time_ms: float
  cache_hit: bool
```

**Key Features:**
- Hybrid retrieval (BM25 + dense vectors)
- LRU caching (500 entries)
- Performance monitoring
- Automatic index management

---

### 3. FAISS Retriever (`retriever/faiss_retriever.py`)

**Purpose:** Vector similarity search using FAISS index

**Input Structure:**
```python
query: str  # Search query
top_k: int  # Number of results
```

**Output Structure:**
```python
List[Dict[str, Any]]  # List of similar documents
# Each result contains:
# - text: str (document text)
# - score: float (similarity score)
# - metadata: Dict (document metadata)
```

**Key Features:**
- Fast vector similarity search
- Configurable similarity metrics
- Metadata preservation
- Batch processing support

---

### 4. Vector Index Builder (`index/build_index.py`)

**Purpose:** Builds and manages FAISS vector index for legal documents

**Input Structure:**
```python
config_path: str  # Configuration file path
index_dir: str  # Output directory for index
```

**Output Structure:**
```python
IndexStats:
  total_documents: int
  total_chunks: int
  index_size_mb: float
  build_time_seconds: float
  embedding_model: str
  index_type: str
```

**Key Features:**
- Automatic document chunking
- Embedding generation
- FAISS index construction
- Metadata persistence
- Performance optimization

---

## 📊 Evidence Management System

### 1. Evidence Verifier (`src/evidence/evidence_verifier.py`)

**Purpose:** Validates reasoning against evidence spans and regulation texts

**Input Structure:**
```python
reasoning_text: str  # Compliance reasoning text
evidence_spans: List[EvidenceSpan]  # Evidence spans
regulation_mappings: List[RegulationMapping]  # Regulation references
```

**Output Structure:**
```python
VerificationResult:
  case_id: str
  reasoning_validation: ReasoningValidation
  evidence_quality: List[EvidenceQuality]
  regulation_mapping_valid: bool
  final_decision: str
  auto_approved: bool
  flags: List[str]
  overall_score: float
```

**Key Features:**
- Automatic evidence validation
- Quality scoring system
- Auto-approval for strong cases
- Flagging for manual review

---

### 2. Evidence Logger (`src/evidence/evidence_logger.py`)

**Purpose:** Logs compliance decisions and evidence for audit trails

**Input Structure:**
```python
decision_data: Dict[str, Any]  # Decision information
evidence_data: Dict[str, Any]  # Supporting evidence
metadata: Dict[str, Any]  # Additional metadata
```

**Output Structure:**
```python
str  # Log entry ID
```

**Key Features:**
- Structured evidence logging
- Automatic redaction
- Retention management
- Audit trail generation

---

### 3. Evidence Monitor (`src/evidence/evidence_monitor.py`)

**Purpose:** Monitors evidence quality and compliance patterns

**Input Structure:**
```python
time_window: Optional[timedelta]  # Monitoring window
thresholds: Dict[str, float]  # Quality thresholds
```

**Output Structure:**
```python
MonitoringReport:
  total_decisions: int
  quality_metrics: Dict[str, float]
  alerts: List[str]
  recommendations: List[str]
```

**Key Features:**
- Real-time quality monitoring
- Automated alerting
- Trend analysis
- Performance optimization

---

### 4. Evidence Analytics (`src/evidence/evidence_analytics.py`)

**Purpose:** Advanced analytics on evidence and compliance data

**Input Structure:**
```python
query_params: Dict[str, Any]  # Analytics query parameters
time_range: Tuple[datetime, datetime]  # Time range for analysis
```

**Output Structure:**
```python
AnalyticsReport:
  summary_stats: Dict[str, Any]
  trends: List[Dict[str, Any]]
  insights: List[str]
  visualizations: List[Dict[str, Any]]
```

**Key Features:**
- Statistical analysis
- Trend identification
- Pattern recognition
- Visualization generation

---

### 5. Evidence Exporter (`src/evidence/evidence_exporter.py`)

**Purpose:** Exports evidence data in various formats

**Input Structure:**
```python
export_config: Dict[str, Any]  # Export configuration
filters: Dict[str, Any]  # Data filters
format: str  # Output format (CSV, JSON, HTML)
```

**Output Structure:**
```python
ExportResult:
  file_path: str
  record_count: int
  export_time: datetime
  format: str
  metadata: Dict[str, Any]
```

**Key Features:**
- Multiple export formats
- Configurable filtering
- Batch processing
- Metadata preservation

---

## 🤖 Compliance Agents

### 1. Active Learning Agent (`src/agents/active_learning_agent.py`)

**Purpose:** Reduces human review effort through active learning

**Input Structure:**
```python
corrections: List[HumanCorrection]  # Human corrections
patterns: List[CorrectionPattern]  # Identified patterns
```

**Output Structure:**
```python
ActiveLearningReport:
  total_corrections: int
  patterns_identified: int
  retraining_recommendations: List[str]
  human_review_reduction: float
  next_actions: List[str]
```

**Key Features:**
- Pattern identification
- Automated retraining triggers
- Performance metrics tracking
- RAG integration for context

---

### 2. Confidence Validator (`src/agents/confidence_validator.py`)

**Purpose:** Validates model confidence scores and triggers human review

**Input Structure:**
```python
predictions: List[Dict[str, Any]]  # Model predictions
confidence_thresholds: Dict[str, float]  # Confidence thresholds
```

**Output Structure:**
```python
ValidationReport:
  validated_predictions: List[Dict[str, Any]]
  flagged_predictions: List[Dict[str, Any]]
  human_review_queue: List[str]
  confidence_metrics: Dict[str, float]
```

**Key Features:**
- Confidence threshold validation
- Automatic flagging
- Human review queue management
- Performance monitoring

---

## 🔄 Data Processing Pipeline

### 1. Document Chunker (`ingest/chunker.py`)

**Purpose:** Intelligent text chunking for legal documents

**Input Structure:**
```python
document: LegalDocument  # Legal document to chunk
config: ChunkingConfig  # Chunking configuration
```

**Output Structure:**
```python
List[TextChunk]  # List of text chunks
# Each chunk contains:
# - text: str (chunk text)
# - metadata: Dict (source, position, etc.)
# - section_label: str (section identifier)
```

**Key Features:**
- Section-aware chunking
- Configurable overlap
- Metadata preservation
- Performance optimization

---

### 2. Document Loader (`ingest/loader.py`)

**Purpose:** Loads and parses legal documents

**Input Structure:**
```python
config_path: str  # Configuration file path
document_paths: List[str]  # Document file paths
```

**Output Structure:**
```python
List[LegalDocument]  # List of loaded documents
# Each document contains:
# - content: str (document text)
# - metadata: Dict (source, date, etc.)
# - law_id: str (regulation identifier)
```

**Key Features:**
- Multiple format support (PDF, DOCX, TXT)
- Automatic format detection
- Metadata extraction
- Error handling

---

### 3. Artifact Preprocessor (`artifact_preprocessor/`)

**Purpose:** Preprocesses artifacts for compliance analysis

**Input Structure:**
```python
documents: List[Path]  # Document paths
terminology: List[Tuple[str, str]]  # Terminology mapping
features: List[Tuple[str, str]]  # Feature descriptions
```

**Output Structure:**
```python
List[DocumentArtifact]  # Preprocessed artifacts
# Each artifact contains:
# - raw_text: str (processed text)
# - expanded_terms: List[str] (expanded terminology)
# - extracted_fields: Dict[str, Any] (extracted information)
```

**Key Features:**
- Multi-format parsing
- Terminology expansion
- Field extraction
- Quality reporting

---

## 📈 Monitoring & Reporting

### 1. Compliance Reporter (`monitoring/reporting/compliance_reporter.py`)

**Purpose:** Generates comprehensive compliance reports

**Input Structure:**
```python
compliance_data: List[FeatureCompliance]  # Compliance data
report_config: Dict[str, Any]  # Report configuration
audience: ReportAudience  # Target audience
```

**Output Structure:**
```python
ComplianceReport:
  report_id: str
  generated_date: str
  summary_stats: Dict[str, Any]
  feature_matrix: List[Dict[str, Any]]
  dashboard_url: Optional[str]
  recommendations: List[str]
```

**Key Features:**
- Multiple report formats
- Audience-specific content
- Dashboard generation
- Automated recommendations

---

### 2. Compliance Analyzer (`monitoring/reporting/compliance_analyzer.py`)

**Purpose:** Analyzes compliance patterns and trends

**Input Structure:**
```python
compliance_data: List[Dict[str, Any]]  # Compliance data
analysis_config: Dict[str, Any]  # Analysis configuration
```

**Output Structure:**
```python
AnalysisReport:
  compliance_summary: Dict[str, Any]
  risk_analysis: Dict[str, Any]
  trend_analysis: List[Dict[str, Any]]
  recommendations: List[str]
```

**Key Features:**
- Pattern recognition
- Risk assessment
- Trend analysis
- Automated insights

---

## 🖥️ CLI Tools

### 1. Artifact Preprocessor CLI (`artifact_preprocessor/cli.py`)

**Purpose:** Command-line interface for artifact preprocessing

**Input Structure:**
```bash
python -m artifact_preprocessor.cli \
  --docs /path/to/documents \
  --terms /path/to/terminology.csv \
  --features /path/to/features.csv \
  --out /path/to/output \
  --log-level INFO
```

**Output Structure:**
```bash
# Generated files:
# - preprocessed.jsonl
# - preprocessed.csv
# - expansion_report.csv
# - processing_report.html
```

**Key Features:**
- Batch processing
- Multiple input formats
- Comprehensive reporting
- Configurable logging

---

### 2. Retriever CLI (`retriever/cli.py`)

**Purpose:** Command-line interface for regulation retrieval

**Input Structure:**
```bash
python -m retriever.cli \
  --query "age verification requirements" \
  --top-k 5 \
  --max-chars 1000 \
  --laws EUDSA,GDPR
```

**Output Structure:**
```bash
# Console output with retrieval results
# - Retrieved text snippets
# - Relevance scores
# - Source information
# - Performance metrics
```

**Key Features:**
- Interactive queries
- Configurable parameters
- Performance monitoring
- Result formatting

---

## 🛠️ Utility Tools

### 1. TikTok Feature Generator (`tiktok_feature_generator.py`)

**Purpose:** Generates synthetic training data for compliance classification

**Input Structure:**
```python
config: Dict[str, Any]  # Generation configuration
templates: List[Dict[str, Any]]  # Feature templates
```

**Output Structure:**
```python
List[GeneratedFeature]  # List of generated features
# Each feature contains:
# - feature_id: str
# - title: str
# - description: str
# - compliance_label: str
# - rationale: str
# - metadata: Dict[str, Any]
```

**Key Features:**
- Realistic feature generation
- Multi-jurisdictional compliance
- Configurable complexity
- Quality validation

---

### 2. Data Scraper (`utils/datascraper.py`)

**Purpose:** Scrapes data from various sources for compliance analysis

**Input Structure:**
```python
urls: List[str]  # URLs to scrape
scraping_config: Dict[str, Any]  # Scraping configuration
```

**Output Structure:**
```python
List[ScrapedData]  # List of scraped data
# Each item contains:
# - content: str (scraped content)
# - metadata: Dict (source, timestamp, etc.)
# - quality_score: float
```

**Key Features:**
- Multiple source support
- Quality scoring
- Rate limiting
- Error handling

---

### 3. PDF Scraper (`utils/pdfscraper.py`)

**Purpose:** Extracts text and metadata from PDF documents

**Input Structure:**
```python
pdf_path: str  # Path to PDF file
extraction_config: Dict[str, Any]  # Extraction configuration
```

**Output Structure:**
```python
PDFExtractionResult:
  text: str (extracted text)
  metadata: Dict (PDF metadata)
  pages: List[str] (page-by-page text)
  tables: List[Dict] (extracted tables)
```

**Key Features:**
- Text extraction
- Metadata extraction
- Table extraction
- OCR support

---

## 🔌 Integration & API Tools

### 1. SDK Client (`sdk/client.py`)

**Purpose:** Python SDK for integrating with compliance services

**Input Structure:**
```python
api_key: str  # API authentication key
base_url: str  # Service base URL
config: Dict[str, Any]  # Client configuration
```

**Output Structure:**
```python
ComplianceClient:
  # Methods for various compliance operations
  - analyze_feature(feature_data)
  - get_compliance_report(report_id)
  - submit_evidence(evidence_data)
  - etc.
```

**Key Features:**
- RESTful API integration
- Authentication handling
- Error handling
- Response parsing

---

### 2. FastAPI Service (`retriever/service.py`)

**Purpose:** Web service for regulation retrieval

**Input Structure:**
```http
POST /retrieve
{
  "query": "age verification requirements",
  "top_k": 5,
  "max_chars": 1000,
  "laws": ["EUDSA", "GDPR"]
}
```

**Output Structure:**
```http
HTTP/1.1 200 OK
{
  "query": "age verification requirements",
  "results": [...],
  "total_results": 5,
  "retrieval_time_ms": 150.5,
  "cache_hit": false
}
```

**Key Features:**
- RESTful API
- JSON request/response
- Performance monitoring
- Caching support

---

## 📊 Data Flow Architecture

```
Input Documents → Preprocessing → Chunking → Embedding → Index Building
                                                      ↓
User Queries → RAG System → Retrieval → Evidence Collection → Compliance Analysis
                                                      ↓
Results → Evidence Logging → Monitoring → Reporting → Active Learning
```

## 🔧 Configuration Management

The system uses YAML-based configuration files:

- **`config.yaml`**: Main system configuration
- **`config/centralized_rag_config.yaml`**: RAG system configuration
- **`config/jurisdictions/`**: Jurisdiction-specific compliance rules

## 🚀 Deployment & Scaling

- **Docker Support**: Containerized deployment
- **Kubernetes**: Scalable orchestration
- **Performance Targets**: P95 latency < 1000ms
- **Caching**: LRU cache with 500 entries
- **Concurrency**: Up to 10 concurrent requests

## 📝 Usage Examples

### Basic Compliance Analysis
```python
from src.models import LLMRAGModel
from src.rag import RAGAdapter

# Initialize model
rag_adapter = RAGAdapter()
model = LLMRAGModel(rag_adapter=rag_adapter)

# Analyze feature
decision, confidence = model.predict("Social media app with age verification")
print(f"Decision: {decision}, Confidence: {confidence}")
```

### Evidence Verification
```python
from src.evidence import EvidenceVerificationAgent

# Initialize verifier
verifier = EvidenceVerificationAgent()

# Verify evidence
result = verifier.verify_reasoning(
    reasoning_text="Feature complies with GDPR Article 7",
    evidence_spans=[...],
    regulation_mappings=[...]
)

print(f"Verification Result: {result.final_decision}")
```

### Active Learning
```python
from src.agents import ActiveLearningAgent

# Initialize agent
agent = ActiveLearningAgent()

# Add human correction
agent.add_human_correction(correction_data)

# Get system status
status = agent.get_system_status()
print(f"Ready for retraining: {status['ready_for_retraining']}")
```

---

## 🔮 Future Enhancements

1. **Multi-language Support**: Expand to non-English regulatory texts
2. **Real-time Updates**: Live regulatory change monitoring
3. **Advanced Analytics**: Machine learning-based compliance insights
4. **Integration APIs**: Third-party platform integrations
5. **Mobile Support**: Mobile compliance monitoring apps

---

*This documentation covers all tools and components in the Geo-Compliance Classifier project as of the current version. For specific implementation details, refer to the individual source files and their docstrings.*

