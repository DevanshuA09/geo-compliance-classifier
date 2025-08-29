"""I/O utilities for file handling and encoding detection."""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import chardet

from .logging_conf import get_logger
from .schema import FeatureRecord

logger = get_logger(__name__)


def detect_encoding(file_path: Path) -> str:
    """Detect file encoding using chardet.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected encoding or 'utf-8' as fallback
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
        
        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0.0)
        
        logger.debug(f"Detected encoding '{encoding}' (confidence: {confidence:.2f}) for {file_path}")
        
        # Fallback to utf-8 if confidence is too low
        if confidence < 0.7:
            logger.warning(f"Low confidence encoding detection for {file_path}, using utf-8")
            return 'utf-8'
            
        return encoding
    except Exception as e:
        logger.warning(f"Failed to detect encoding for {file_path}: {e}, using utf-8")
        return 'utf-8'


def read_text_file(file_path: Path, encoding: Optional[str] = None) -> str:
    """Read text file with encoding detection.
    
    Args:
        file_path: Path to the file
        encoding: Optional encoding override
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file cannot be decoded
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if encoding is None:
        encoding = detect_encoding(file_path)
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError as e:
        logger.warning(f"Failed to decode {file_path} with {encoding}, trying utf-8 with errors='ignore'")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()


def load_terminology_csv(file_path: Path) -> Dict[str, str]:
    """Load terminology mapping from CSV file.
    
    Args:
        file_path: Path to terminology CSV file
        
    Returns:
        Dictionary mapping terms to explanations
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Terminology file not found: {file_path}")
    
    terminology = {}
    encoding = detect_encoding(file_path)
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            
            # Validate required columns
            if 'term' not in reader.fieldnames or 'explanation' not in reader.fieldnames:
                raise ValueError(f"CSV must have 'term' and 'explanation' columns. Found: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, 1):
                term = row['term'].strip()
                explanation = row['explanation'].strip()
                
                if not term:
                    logger.warning(f"Empty term in row {row_num}, skipping")
                    continue
                
                if not explanation:
                    logger.warning(f"Empty explanation for term '{term}' in row {row_num}")
                
                terminology[term] = explanation
                
        logger.info(f"Loaded {len(terminology)} terms from {file_path}")
        return terminology
        
    except Exception as e:
        raise ValueError(f"Failed to parse terminology CSV {file_path}: {e}")


def load_features_csv(file_path: Path) -> List[Tuple[str, str]]:
    """Load features from CSV file.
    
    Args:
        file_path: Path to features CSV file
        
    Returns:
        List of (feature_name, feature_description) tuples
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Features file not found: {file_path}")
    
    features = []
    encoding = detect_encoding(file_path)
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            
            # Validate required columns
            if 'feature_name' not in reader.fieldnames or 'feature_description' not in reader.fieldnames:
                raise ValueError(f"CSV must have 'feature_name' and 'feature_description' columns. Found: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, 1):
                name = row['feature_name'].strip()
                description = row['feature_description'].strip()
                
                if not name:
                    logger.warning(f"Empty feature_name in row {row_num}, skipping")
                    continue
                
                features.append((name, description))
                
        logger.info(f"Loaded {len(features)} features from {file_path}")
        return features
        
    except Exception as e:
        raise ValueError(f"Failed to parse features CSV {file_path}: {e}")


def write_jsonl(records: List[FeatureRecord], output_path: Path) -> None:
    """Write records to JSONL file.
    
    Args:
        records: List of feature records
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            json.dump(record.to_dict(), f, ensure_ascii=False)
            f.write('\n')
    
    logger.info(f"Wrote {len(records)} records to {output_path}")


def write_csv(records: List[FeatureRecord], output_path: Path) -> None:
    """Write records to CSV file.
    
    Args:
        records: List of feature records
        output_path: Output file path
    """
    if not records:
        logger.warning("No records to write to CSV")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get all field names from the first record
    fieldnames = list(records[0].to_dict().keys())
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            row_dict = record.to_dict()
            # Convert list fields to JSON strings for CSV compatibility
            if isinstance(row_dict.get('codename_hits_json'), list):
                row_dict['codename_hits_json'] = json.dumps(row_dict['codename_hits_json'])
            writer.writerow(row_dict)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")


def find_documents(docs_dir: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """Find all document files in directory.
    
    Args:
        docs_dir: Directory to search
        extensions: List of file extensions to include
        
    Returns:
        List of document file paths
    """
    if extensions is None:
        extensions = ['.pdf', '.docx', '.md', '.html', '.txt']
    
    documents = []
    if docs_dir.exists() and docs_dir.is_dir():
        for ext in extensions:
            documents.extend(docs_dir.glob(f"**/*{ext}"))
    
    logger.info(f"Found {len(documents)} documents in {docs_dir}")
    return sorted(documents)  # Deterministic ordering
