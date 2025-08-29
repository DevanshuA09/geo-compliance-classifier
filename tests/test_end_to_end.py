"""End-to-end integration tests."""

import pytest
import tempfile
import csv
import json
from pathlib import Path

from artifact_preprocessor.cli import main
from artifact_preprocessor.io_utils import load_terminology_csv, load_features_csv


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Create temporary directory with test data."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create terminology CSV
        terms_file = temp_dir / "terminology.csv"
        with open(terms_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['term', 'explanation'])
            writer.writerow(['ASL', 'Age-sensitive logic'])
            writer.writerow(['PF', 'Personalized feed'])
            writer.writerow(['GH', 'Geo-handler; a module responsible for routing features'])
            writer.writerow(['CDS', 'Compliance Detection System'])
        
        # Create features CSV
        features_file = temp_dir / "features.csv"
        with open(features_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['feature_name', 'feature_description'])
            writer.writerow(['Test Feature 1', 'This feature uses PF and ASL for user detection.'])
            writer.writerow(['Test Feature 2', 'GH routing with CDS monitoring for compliance.'])
        
        # Create sample documents
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        
        # Text document
        with open(docs_dir / "test.txt", 'w', encoding='utf-8') as f:
            f.write("""
            Feature: Advanced Search
            
            Description: This feature provides search capabilities using PF algorithms.
            
            Objectives:
            - Improve search accuracy
            - Reduce response time
            
            User Segments: All users with ASL-based age verification
            
            Geo Regions: US, EU, CA
            """)
        
        # Markdown document
        with open(docs_dir / "spec.md", 'w', encoding='utf-8') as f:
            f.write("""
            # Feature Specification
            
            ## Overview
            This document describes the GH implementation for regional routing.
            
            ## Risk Assessment
            Medium risk due to CDS integration requirements.
            
            ## Privacy Data
            Collects minimal user location data for GH routing.
            """)
        
        yield temp_dir, terms_file, features_file, docs_dir
        
        # Cleanup is handled by tempfile
    
    def test_cli_features_only(self, test_data_dir):
        """Test CLI with features CSV only."""
        temp_dir, terms_file, features_file, docs_dir = test_data_dir
        output_dir = temp_dir / "output"
        
        # Run CLI
        import sys
        original_argv = sys.argv
        try:
            sys.argv = [
                'cli.py',
                '--features', str(features_file),
                '--terms', str(terms_file),
                '--out', str(output_dir)
            ]
            
            result = main()
            assert result == 0
            
        finally:
            sys.argv = original_argv
        
        # Verify outputs exist
        assert (output_dir / "preprocessed.jsonl").exists()
        assert (output_dir / "preprocessed.csv").exists()
        assert (output_dir / "expansion_report.csv").exists()
        assert (output_dir / "report.md").exists()
        
        # Verify JSONL content
        with open(output_dir / "preprocessed.jsonl", 'r', encoding='utf-8') as f:
            records = [json.loads(line) for line in f]
        
        assert len(records) == 2
        
        # Check first record
        record1 = records[0]
        assert record1['feature_id'] == 'csv_feature_0000'
        assert record1['doc_type'] == 'csv'
        assert 'Test Feature 1' in record1['feature_title']
        assert 'PF and ASL' in record1['feature_description']
        assert len(record1['codename_hits_json']) >= 2  # Should find PF and ASL
        
        # Verify expansion report
        with open(output_dir / "expansion_report.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            expansion_rows = list(reader)
        
        assert len(expansion_rows) >= 4  # At least 2 terms x 2 features
        
        # Check for expected terms
        found_terms = set(row['term'] for row in expansion_rows)
        assert 'PF' in found_terms
        assert 'ASL' in found_terms
    
    def test_cli_docs_only(self, test_data_dir):
        """Test CLI with documents only."""
        temp_dir, terms_file, features_file, docs_dir = test_data_dir
        output_dir = temp_dir / "output2"
        
        import sys
        original_argv = sys.argv
        try:
            sys.argv = [
                'cli.py',
                '--docs', str(docs_dir),
                '--terms', str(terms_file),
                '--out', str(output_dir)
            ]
            
            result = main()
            assert result == 0
            
        finally:
            sys.argv = original_argv
        
        # Verify outputs exist
        assert (output_dir / "preprocessed.jsonl").exists()
        assert (output_dir / "report.md").exists()
        
        # Verify document processing
        with open(output_dir / "preprocessed.jsonl", 'r', encoding='utf-8') as f:
            records = [json.loads(line) for line in f]
        
        assert len(records) == 2  # Two documents
        
        # Check document types
        doc_types = [r['doc_type'] for r in records]
        assert 'txt' in doc_types
        assert 'md' in doc_types
        
        # Verify field extraction worked
        txt_record = next(r for r in records if r['doc_type'] == 'txt')
        assert txt_record['feature_title'] is not None
        assert txt_record['objectives'] is not None
        assert txt_record['user_segments'] is not None
    
    def test_cli_combined(self, test_data_dir):
        """Test CLI with both features and documents."""
        temp_dir, terms_file, features_file, docs_dir = test_data_dir
        output_dir = temp_dir / "output3"
        
        import sys
        original_argv = sys.argv
        try:
            sys.argv = [
                'cli.py',
                '--features', str(features_file),
                '--docs', str(docs_dir),
                '--terms', str(terms_file),
                '--out', str(output_dir),
                '--verbose'  # Test verbose logging
            ]
            
            result = main()
            assert result == 0
            
        finally:
            sys.argv = original_argv
        
        # Verify combined processing
        with open(output_dir / "preprocessed.jsonl", 'r', encoding='utf-8') as f:
            records = [json.loads(line) for line in f]
        
        # Should have records from both CSV (2) and docs (2)
        assert len(records) == 4
        
        # Verify mix of sources
        sources = set(r['doc_type'] for r in records)
        assert 'csv' in sources
        assert 'txt' in sources
        assert 'md' in sources
    
    def test_parse_success_rate(self, test_data_dir):
        """Test that parse success rate meets 100% threshold for well-formed inputs."""
        temp_dir, terms_file, features_file, docs_dir = test_data_dir
        output_dir = temp_dir / "output4"
        
        import sys
        original_argv = sys.argv
        try:
            sys.argv = [
                'cli.py',
                '--features', str(features_file),
                '--docs', str(docs_dir),
                '--terms', str(terms_file),
                '--out', str(output_dir)
            ]
            
            result = main()
            # Should succeed with 100% parse rate for well-formed inputs
            assert result == 0
            
        finally:
            sys.argv = original_argv
        
        # Verify report contains success metrics
        report_file = output_dir / "report.md"
        assert report_file.exists()
        
        report_content = report_file.read_text(encoding='utf-8')
        assert "Parse success rate" in report_content
        assert "100.0%" in report_content or "100%" in report_content
    
    def test_output_schema_compliance(self, test_data_dir):
        """Test that outputs comply with the expected schema."""
        temp_dir, terms_file, features_file, docs_dir = test_data_dir
        output_dir = temp_dir / "output5"
        
        import sys
        original_argv = sys.argv
        try:
            sys.argv = [
                'cli.py',
                '--features', str(features_file),
                '--terms', str(terms_file),
                '--out', str(output_dir)
            ]
            
            result = main()
            assert result == 0
            
        finally:
            sys.argv = original_argv
        
        # Verify JSONL schema compliance
        with open(output_dir / "preprocessed.jsonl", 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                
                # Check required fields
                required_fields = [
                    'feature_id', 'doc_id', 'doc_type', 'text_original_hash',
                    'text_expanded_hash', 'codename_hits_json', 'parse_warnings', 'source_path'
                ]
                for field in required_fields:
                    assert field in record
                
                # Check codename hits structure
                for hit in record['codename_hits_json']:
                    assert 'term' in hit
                    assert 'expansion' in hit
                    assert 'count' in hit
                    assert 'spans' in hit
                    assert isinstance(hit['count'], int)
                    assert isinstance(hit['spans'], list)
        
        # Verify CSV has same data
        with open(output_dir / "preprocessed.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_records = list(reader)
        
        with open(output_dir / "preprocessed.jsonl", 'r', encoding='utf-8') as f:
            jsonl_records = [json.loads(line) for line in f]
        
        assert len(csv_records) == len(jsonl_records)
    
    def test_error_handling(self, test_data_dir):
        """Test graceful error handling with invalid inputs."""
        temp_dir, terms_file, features_file, docs_dir = test_data_dir
        
        # Test with missing terminology file
        import sys
        original_argv = sys.argv
        try:
            sys.argv = [
                'cli.py',
                '--features', str(features_file),
                '--terms', '/nonexistent/terms.csv',
                '--out', str(temp_dir / "output_error")
            ]
            
            result = main()
            # Should fail gracefully
            assert result == 1
            
        finally:
            sys.argv = original_argv


class TestWellFormedInputs:
    """Test the definition of 'well-formed' inputs and success criteria."""
    
    def test_well_formed_csv(self):
        """Test that well-formed CSV inputs are properly defined."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create well-formed CSV
        features_file = temp_dir / "features.csv"
        with open(features_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['feature_name', 'feature_description'])
            writer.writerow(['Valid Feature', 'This is a valid, readable feature description.'])
        
        # Load and verify
        features = load_features_csv(features_file)
        assert len(features) == 1
        assert features[0][0] == 'Valid Feature'
        assert len(features[0][1]) > 10  # Has meaningful description
    
    def test_well_formed_terminology(self):
        """Test that well-formed terminology is properly defined."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create well-formed terminology
        terms_file = temp_dir / "terms.csv"
        with open(terms_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['term', 'explanation'])
            writer.writerow(['ASL', 'Age-sensitive logic'])
            writer.writerow(['PF', 'Personalized feed'])
        
        # Load and verify
        terminology = load_terminology_csv(terms_file)
        assert len(terminology) == 2
        assert all(len(term) > 0 for term in terminology.keys())
        assert all(len(explanation) > 0 for explanation in terminology.values())
    
    def test_well_formed_documents(self):
        """Test that well-formed documents are properly processed."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create well-formed text document
        doc_file = temp_dir / "test.txt"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write("Feature: Test Feature\n\nThis is a readable document with proper structure.")
        
        # Import and test parser
        from artifact_preprocessor.parsers.txt_parser import parse_txt
        
        result = parse_txt(doc_file)
        assert len(result.raw_text) > 0
        assert len(result.parse_warnings) == 0  # Well-formed should have no warnings
        assert result.doc_type == 'txt'
