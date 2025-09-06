#!/usr/bin/env python3
"""
Test Stage 1: Entity Collection & Normalization for FSH edge.
"""

import pytest
import tempfile
import json
import os
from phase1 import stage1_entity_collection_and_normalization


def test_stage1_fsh_edge_normalization():
    """Test Stage 1 normalization for FSH edge with expected results."""
    
    # Create test FSH edge
    edge = {
        'subject': 'CHEBI:81569',  # FSH receptor 
        'object': 'UniProtKB:P80370',  # Some protein
        'sentences': 'FSH stimulation increased protein X expression.'
    }
    
    # Create temporary edges file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps(edge) + '\n')
        edges_file = f.name
    
    try:
        # Run Stage 1
        entities, normalized_data = stage1_entity_collection_and_normalization(edges_file, max_edges=1)
        
        # Verify collected entities
        assert len(entities) == 2
        assert 'CHEBI:81569' in entities
        assert 'UniProtKB:P80370' in entities
        
        # Verify normalization results
        assert 'CHEBI:81569' in normalized_data
        assert 'UniProtKB:P80370' in normalized_data
        
        # Test CHEBI normalization
        gtopdb_norm = normalized_data['CHEBI:81569']
        assert gtopdb_norm['id']['identifier'] == 'CHEBI:81569'  # Should normalize to itself
        # Check if FSH appears as a label in any of the equivalent_identifiers
        fsh_found = False
        for equiv_id in gtopdb_norm['equivalent_identifiers']:
            if equiv_id.get('label') == 'FSH':
                fsh_found = True
                break
        assert fsh_found, "FSH label should be found in equivalent_identifiers"
        assert 'biolink:ChemicalEntity' in gtopdb_norm['type']  # Should be chemical type
        
        # Test UniProtKB:P80370 normalization  
        uniprot_norm = normalized_data['UniProtKB:P80370']
        assert uniprot_norm['id']['identifier'] == 'NCBIGene:8788'  # Should normalize to NCBIGene:8788
        assert uniprot_norm['id']['label'] == 'DLK1'  # Should have DLK1 label
        assert 'biolink:Gene' in uniprot_norm['type']  # Should be gene type
        
    finally:
        # Clean up
        os.unlink(edges_file)


def test_stage1_entity_collection():
    """Test Stage 1 entity collection from multiple edges."""
    
    # Create test edges with overlapping entities
    edges = [
        {'subject': 'GTOPDB:4386', 'object': 'UniProtKB:P80370', 'sentences': 'test1'},
        {'subject': 'GTOPDB:4386', 'object': 'CHEBI:123', 'sentences': 'test2'},  # Overlapping subject
        {'subject': 'TEST:456', 'object': 'UniProtKB:P80370', 'sentences': 'test3'}   # Overlapping object
    ]
    
    # Create temporary edges file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for edge in edges:
            f.write(json.dumps(edge) + '\n')
        edges_file = f.name
    
    try:
        # Run Stage 1
        entities, normalized_data = stage1_entity_collection_and_normalization(edges_file, max_edges=3)
        
        # Verify unique entity collection
        expected_entities = {'GTOPDB:4386', 'UniProtKB:P80370', 'CHEBI:123', 'TEST:456'}
        assert len(entities) == 4
        assert set(entities) == expected_entities
        
        # Verify all entities were normalized (or attempted)
        assert len(normalized_data) == 4
        for entity in expected_entities:
            assert entity in normalized_data
        
        print("✅ Stage 1 entity collection results:")
        print(f"   Collected {len(entities)} unique entities from 3 edges")
        print(f"   Entities: {entities}")
        
    finally:
        # Clean up
        os.unlink(edges_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
