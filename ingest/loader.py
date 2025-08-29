"""
Legal document ingestion and normalization pipeline.
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml

from retriever.models import LegalDocument, Jurisdiction


logger = logging.getLogger(__name__)


class DocumentLoader:
    """Loads and normalizes legal documents with section detection."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize loader with configuration."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.sources = self.config['sources']
        self.section_patterns = {}
        
        # Compile regex patterns for each law
        for law_id, source_config in self.sources.items():
            patterns = source_config.get('section_patterns', [])
            self.section_patterns[law_id] = [re.compile(pattern, re.IGNORECASE) 
                                           for pattern in patterns]
    
    def load_all_documents(self) -> List[LegalDocument]:
        """Load all configured legal documents."""
        documents = []
        
        for law_id, source_config in self.sources.items():
            try:
                doc = self.load_document(law_id)
                documents.append(doc)
                logger.info(f"Loaded {law_id}: {len(doc.content)} chars, {doc.total_lines} lines")
            except Exception as e:
                logger.error(f"Failed to load {law_id}: {e}")
                raise
        
        return documents
    
    def load_document(self, law_id: str) -> LegalDocument:
        """Load a specific legal document by ID."""
        if law_id not in self.sources:
            raise ValueError(f"Unknown law_id: {law_id}")
        
        source_config = self.sources[law_id]
        file_path = Path(source_config['file_path'])
        
        if not file_path.exists():
            raise FileNotFoundError(f"Legal document not found: {file_path}")
        
        # Read and normalize content
        content = self._read_and_normalize(file_path)
        
        return LegalDocument(
            law_id=law_id,
            law_name=source_config['law_name'],
            jurisdiction=Jurisdiction(source_config['jurisdiction']),
            source_path=str(file_path),
            content=content,
            total_lines=len(content.splitlines())
        )
    
    def _read_and_normalize(self, file_path: Path) -> str:
        """Read file with encoding detection and normalize text."""
        # Try UTF-8 first, then detect encoding
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with chardet if available
            try:
                import chardet
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
                content = raw_data.decode(encoding or 'utf-8', errors='ignore')
            except ImportError:
                # Fallback to utf-8 with error handling
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
        
        # Normalize whitespace and line endings
        content = re.sub(r'\\r\\n?', '\\n', content)  # Normalize line endings
        content = re.sub(r'\\n{3,}', '\\n\\n', content)  # Collapse multiple newlines
        content = re.sub(r'[ \\t]+', ' ', content)  # Normalize spaces
        
        return content.strip()
    
    def detect_sections(self, law_id: str, content: str) -> List[Tuple[str, int, int]]:
        """
        Detect section boundaries in legal text.
        
        Returns:
            List of (section_label, start_line, end_line) tuples
        """
        if law_id not in self.section_patterns:
            return [("Document", 0, len(content.splitlines()) - 1)]
        
        lines = content.splitlines()
        sections = []
        patterns = self.section_patterns[law_id]
        
        current_section = None
        current_start = 0
        
        for line_num, line in enumerate(lines):
            # Check if line contains a section header
            for pattern in patterns:
                match = pattern.search(line.strip())
                if match:
                    # Close previous section
                    if current_section:
                        sections.append((current_section, current_start, line_num - 1))
                    
                    # Start new section
                    current_section = match.group(0)
                    current_start = line_num
                    break
        
        # Close final section
        if current_section:
            sections.append((current_section, current_start, len(lines) - 1))
        
        # If no sections found, treat entire document as one section
        if not sections:
            sections = [("Document", 0, len(lines) - 1)]
        
        logger.info(f"Detected {len(sections)} sections in {law_id}")
        return sections
    
    def get_section_hierarchy(self, law_id: str, section_label: str) -> str:
        """
        Generate hierarchical section path for better navigation.
        
        Args:
            law_id: Legal document identifier
            section_label: Section label (e.g., "§501.1736(2)(a)")
            
        Returns:
            Hierarchical path (e.g., "§501.1736 > (2) > (a)")
        """
        # Simple hierarchy detection based on common patterns
        if '(' in section_label and ')' in section_label:
            # Extract nested subsections
            base = section_label.split('(')[0]
            subsections = re.findall(r'\\((\\w+)\\)', section_label)
            if subsections:
                hierarchy_parts = [base.strip()]
                for sub in subsections:
                    hierarchy_parts.append(f"({sub})")
                return " > ".join(hierarchy_parts)
        
        return section_label
