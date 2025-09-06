"""
Integration test for classification constants that would have caught the synonyms processing bug.

This test verifies that the classification system works end-to-end with real data
and produces a reasonable distribution of classifications, not all one type.
"""

import json
import tempfile
import os
from pathlib import Path
import pytest

from phase1 import (
    CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS,
    CLASSIFICATIONS, CLASSIFICATION_FILE_MAPPING, process_efficient_batch
)


class TestClassificationConstantsIntegration:
    """Integration tests for classification constants and end-to-end processing."""
    
    def setup_method(self):
        """Set up test data that should produce a mix of classifications."""
        # Create realistic test edges that should produce different classifications
        self.test_edges = [
            # Edge that should PASS (both entities clearly in text)
            {
                "subject": "CHEBI:28748",  # doxorubicin
                "object": "UniProtKB:P18887",  # XRCC1
                "sentences": "The significant increase in CDKN1A and XRCC1 suggest a cell cycle arrest and implies an alternative NHEJ pathway in response to doxorubicin-induced DNA breaks.",
                "predicate": "biolink:affects"
            },
            # Edge that should be AMBIGUOUS (multiple interpretations)
            {
                "subject": "CHEBI:16199",  # uridine
                "object": "HGNC:12445",   # UPP1
                "sentences": "UMP phosphorylase catalyzes the conversion of uracil to UMP in the presence of ribose-1-phosphate.",
                "predicate": "biolink:affects"
            },
            # Edge that should be UNRESOLVED (entities not found in text)
            {
                "subject": "CHEBI:15365",  # aspirin
                "object": "HGNC:9604",    # PTGS1 (COX1)
                "sentences": "The study examined cardiac function and blood pressure in patients with diabetes.",
                "predicate": "biolink:affects"
            },
            # Another edge that should PASS
            {
                "subject": "CHEBI:6807",   # metformin  
                "object": "HGNC:5334",    # HMGCR
                "sentences": "Metformin treatment significantly reduced HMGCR expression and cholesterol synthesis in hepatic cells.",
                "predicate": "biolink:affects"
            },
        ]
        
        # Create test nodes data
        self.test_nodes = {
            "CHEBI:28748": {"id": "CHEBI:28748", "name": "doxorubicin", "category": "biolink:SmallMolecule"},
            "UniProtKB:P18887": {"id": "UniProtKB:P18887", "name": "XRCC1", "category": "biolink:Protein"},
            "CHEBI:16199": {"id": "CHEBI:16199", "name": "uridine", "category": "biolink:SmallMolecule"},
            "HGNC:12445": {"id": "HGNC:12445", "name": "UPP1", "category": "biolink:Gene"},
            "CHEBI:15365": {"id": "CHEBI:15365", "name": "aspirin", "category": "biolink:SmallMolecule"},
            "HGNC:9604": {"id": "HGNC:9604", "name": "PTGS1", "category": "biolink:Gene"},
            "CHEBI:6807": {"id": "CHEBI:6807", "name": "metformin", "category": "biolink:SmallMolecule"},
            "HGNC:5334": {"id": "HGNC:5334", "name": "HMGCR", "category": "biolink:Gene"},
        }

    def test_classification_constants_are_valid(self):
        """Test that all classification constants are properly defined."""
        # Test constants exist and are strings
        assert isinstance(CLASSIFICATION_PASSED, str)
        assert isinstance(CLASSIFICATION_UNRESOLVED, str) 
        assert isinstance(CLASSIFICATION_AMBIGUOUS, str)
        
        # Test constants are not empty
        assert CLASSIFICATION_PASSED.strip()
        assert CLASSIFICATION_UNRESOLVED.strip()
        assert CLASSIFICATION_AMBIGUOUS.strip()
        
        # Test constants are distinct
        constants = {CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS}
        assert len(constants) == 3, "Classification constants must be distinct"
        
        # Test CLASSIFICATIONS set contains all constants
        assert CLASSIFICATION_PASSED in CLASSIFICATIONS
        assert CLASSIFICATION_UNRESOLVED in CLASSIFICATIONS
        assert CLASSIFICATION_AMBIGUOUS in CLASSIFICATIONS
        
        # Test file mapping contains all constants
        assert CLASSIFICATION_PASSED in CLASSIFICATION_FILE_MAPPING
        assert CLASSIFICATION_UNRESOLVED in CLASSIFICATION_FILE_MAPPING
        assert CLASSIFICATION_AMBIGUOUS in CLASSIFICATION_FILE_MAPPING
        
        # Test file mapping values are valid filenames (no spaces, special chars)
        for file_name in CLASSIFICATION_FILE_MAPPING.values():
            assert ' ' not in file_name, f"File name '{file_name}' should not contain spaces"
            assert file_name.replace('_', '').replace('-', '').isalnum(), f"File name '{file_name}' should only contain alphanumeric, underscore, hyphen"

    def test_end_to_end_classification_produces_mixed_results(self):
        """
        Critical integration test that would have caught the synonyms bug.
        
        This test verifies that:
        1. The classification pipeline works end-to-end
        2. We get a reasonable distribution of results (not all one type)  
        3. Each classification constant is used properly
        """
        # Create temporary output files
        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = {}
            for classification in CLASSIFICATIONS:
                file_path = Path(temp_dir) / f"{CLASSIFICATION_FILE_MAPPING[classification]}.jsonl"
                output_files[classification] = open(file_path, 'w')
            
            try:
                # Process test edges through the batch processing pipeline
                # This is the same code path that was broken
                # Initialize empty global caches (will be populated by the function)
                global_normalized_cache = {}
                global_synonyms_cache = {}
                
                process_efficient_batch(
                    self.test_edges, 
                    self.test_nodes, 
                    output_files,
                    global_normalized_cache,
                    global_synonyms_cache
                )
                
                # Close files to flush writes
                for f in output_files.values():
                    f.close()
                
                # Read results and count classifications
                classification_counts = {classification: 0 for classification in CLASSIFICATIONS}
                
                for classification in CLASSIFICATIONS:
                    file_path = Path(temp_dir) / f"{CLASSIFICATION_FILE_MAPPING[classification]}.jsonl"
                    if file_path.exists():
                        with open(file_path, 'r') as f:
                            for line in f:
                                if line.strip():
                                    edge_data = json.loads(line)
                                    assert 'qc_classification' in edge_data, "Edge must have qc_classification field"
                                    edge_classification = edge_data['qc_classification']
                                    assert edge_classification == classification, f"Edge in {classification} file must have qc_classification={classification}"
                                    classification_counts[classification] += 1
                
                # Verify we processed all test edges
                total_processed = sum(classification_counts.values())
                assert total_processed == len(self.test_edges), f"Expected to process {len(self.test_edges)} edges, got {total_processed}"
                
                # CRITICAL TEST: Verify we got a reasonable distribution
                # This would have caught the bug where everything was classified as UNRESOLVED
                assert classification_counts[CLASSIFICATION_UNRESOLVED] < len(self.test_edges), \
                    f"Too many edges classified as unresolved ({classification_counts[CLASSIFICATION_UNRESOLVED]}/{len(self.test_edges)}). " \
                    f"This suggests a bug in synonyms processing or classification logic. " \
                    f"Distribution: {classification_counts}"
                
                # We should have at least one passed edge (with our test data that has clear matches)
                assert classification_counts[CLASSIFICATION_PASSED] > 0, \
                    f"Expected at least one '{CLASSIFICATION_PASSED}' edge with test data containing clear entity matches. " \
                    f"Got distribution: {classification_counts}"
                
                print(f"✅ Classification distribution: {classification_counts}")
                
            finally:
                # Ensure all files are closed
                for f in output_files.values():
                    if not f.closed:
                        f.close()

    def test_synonyms_data_key_consistency(self):
        """
        Test that would have caught the specific synonyms key mismatch bug.
        
        This verifies that synonyms_data uses normalized entity IDs as keys,
        not original entity IDs.
        """
        # Mock data to simulate the bug scenario
        edge = {
            "subject": "UniProtKB:P18887",  # Original ID
            "object": "CHEBI:28748",
            "sentences": "XRCC1 and doxorubicin interaction"
        }
        
        # Simulate normalized data (what we get from normalization API)
        normalized_data = {
            "UniProtKB:P18887": {
                "id": {"identifier": "NCBIGene:7515"},  # Normalized ID
                "equivalent_identifiers": [{"identifier": "NCBIGene:7515"}]
            },
            "CHEBI:28748": {
                "id": {"identifier": "CHEBI:28748"},
                "equivalent_identifiers": [{"identifier": "CHEBI:28748"}]
            }
        }
        
        # Simulate synonyms data (uses normalized IDs as keys)
        synonyms_data = {
            "NCBIGene:7515": {  # Must use normalized ID, not original "UniProtKB:P18887"
                "names": ["XRCC1", "RCC"],
                "types": ["Protein"]
            },
            "CHEBI:28748": {
                "names": ["doxorubicin", "DOX"],
                "types": ["SmallMolecule"] 
            }
        }
        
        # Import classify_edge to test the core logic
        from phase1 import classify_edge
        
        # This should work without throwing "Missing synonyms" error
        classification, debug_info = classify_edge(edge, {}, normalized_data, synonyms_data)
        
        # Should not be unresolved due to missing synonyms
        assert classification != CLASSIFICATION_UNRESOLVED or \
               "Missing synonyms" not in debug_info.get('reason', ''), \
               f"Classification failed due to synonyms key mismatch. Got: {classification}, reason: {debug_info.get('reason')}"
        
        print(f"✅ Synonyms key consistency test passed: {classification}")

    def test_file_mapping_creates_valid_filenames(self):
        """Test that CLASSIFICATION_FILE_MAPPING produces valid filenames."""
        for classification, filename in CLASSIFICATION_FILE_MAPPING.items():
            # Test filename is valid
            assert filename, f"Filename for {classification} should not be empty"
            assert not filename.startswith('.'), f"Filename '{filename}' should not start with dot"
            
            # Test we can create a file with this name
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = Path(temp_dir) / f"{filename}.jsonl"
                
                # Should be able to create and write to file
                with open(file_path, 'w') as f:
                    f.write('test\n')
                
                # Should be able to read from file
                with open(file_path, 'r') as f:
                    content = f.read()
                    assert content == 'test\n'