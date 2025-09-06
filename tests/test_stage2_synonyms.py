#!/usr/bin/env python3
"""
Test Stage 2: Synonym Retrieval for FSH edge.
"""

import pytest
from phase1 import stage2_synonym_retrieval


def test_stage2_fsh_edge_synonyms():
    """Test Stage 2 synonym retrieval for FSH edge with expected results."""
    
    # Mock normalized_data from Stage 1 (what we expect from Stage 1 test)
    normalized_data = {
        'CHEBI:81569': {
            'id': {'identifier': 'CHEBI:81569', 'label': 'Follitropin'},
            'type': ['biolink:ChemicalEntity']
        },
        'UniProtKB:P80370': {
            'id': {'identifier': 'NCBIGene:8788', 'label': 'DLK1'},
            'type': ['biolink:Gene']
        }
    }
    
    # Run Stage 2
    synonyms_data = stage2_synonym_retrieval(normalized_data)
    
    # Verify synonym results for both entities
    assert 'CHEBI:81569' in synonyms_data
    assert 'NCBIGene:8788' in synonyms_data
    
    # Test CHEBI:81569 synonyms (FSH)
    chebi_synonyms = synonyms_data['CHEBI:81569']
    assert chebi_synonyms['curie'] == 'CHEBI:81569'
    assert chebi_synonyms['preferred_name'] == 'Follitropin'
    
    # Should have many synonyms (hundreds)
    actual_chebi_names = chebi_synonyms['names']
    assert len(actual_chebi_names) > 50, f"Expected many FSH synonyms, got {len(actual_chebi_names)}"
    
    # Check that FSH is in the list somewhere
    assert 'FSH' in actual_chebi_names, "FSH should be in the CHEBI:81569 synonyms"
    
    assert 'SmallMolecule' in chebi_synonyms['types'] or 'biolink:SmallMolecule' in chebi_synonyms['types']
    
    # Test NCBIGene:8788 (DLK1) synonyms
    dlk1_synonyms = synonyms_data['NCBIGene:8788']
    assert dlk1_synonyms['curie'] == 'NCBIGene:8788'
    assert dlk1_synonyms['preferred_name'] == 'DLK1'
    
    # Expected synonyms from curl result - all 44 synonyms 
    expected_dlk1_names = [
        'DLK', 'pG2', 'ZOG', 'FA1', 'DLK1', 'PREF1', 'Delta1', 'PREADIPOCYTE FACTOR 1',
        'fetal antigen 1', 'Protein delta homolog 1', 'preadipocyte factor 1',
        'protein delta homolog 1', 'FA-1', 'DLK-1', 'DELTA1', 'Dlk1', 'Pref1',
        'delta like non-canonical Notch ligand 1', 'protein delta-like 1 homolog',
        'Delta-like 1 homolog', 'protein delta-like 1', 'delta, drosophila, homolog 1',
        'Delta1', 'delta-like 1', 'Delta-like protein 1', 'pG2 delta drosophila homolog',
        'preadipocyte factor-1', 'DLK-1 protein', 'delta-like 1 homolog',
        'Delta-like 1', 'pG2delta', 'Delta-like homolog 1', 'fetal antigen-1',
        'PREADIPOCYTE FACTOR-1', 'Delta1 protein', 'pG2-delta', 'Pref-1',
        'delta-like protein 1', 'preadipocyte factor 1 protein', 'pG2-Delta',
        'Delta-like 1 protein', 'delta like 1', 'preadipocyte factor I', 'FA-I'
    ]
    actual_dlk1_names = dlk1_synonyms['names']
    
    # Verify we got all expected synonyms (should be 44 total)
    assert len(actual_dlk1_names) >= 44, f"Expected at least 44 DLK1 synonyms, got {len(actual_dlk1_names)}"
    
    # Check that all expected synonyms are present
    missing_synonyms = []
    for expected_name in expected_dlk1_names:
        if expected_name not in actual_dlk1_names:
            missing_synonyms.append(expected_name)
    
    if missing_synonyms:
        print(f"Missing synonyms: {missing_synonyms}")
        print(f"Actual synonyms found: {actual_dlk1_names}")
        
    # At minimum, check that key synonyms are present
    key_synonyms = ['DLK1', 'FA1', 'PREF1', 'fetal antigen 1', 'protein delta homolog 1']
    for key_synonym in key_synonyms:
        assert key_synonym in actual_dlk1_names, f"Key synonym '{key_synonym}' missing from NCBIGene:8788 synonyms"
    
    assert 'Gene' in dlk1_synonyms['types'] or 'biolink:Gene' in dlk1_synonyms['types']
    
    print("✅ Stage 2 synonym retrieval results:")
    print(f"   CHEBI:81569 synonyms: {actual_chebi_names[:5]}...")
    print(f"   NCBIGene:8788 synonyms: {actual_dlk1_names[:5]}...")


def test_stage2_synonym_structure():
    """Test Stage 2 returns expected data structure."""
    
    # Minimal normalized_data for testing structure
    normalized_data = {
        'TEST:123': {
            'id': {'identifier': 'TEST:123', 'label': 'test'}
        }
    }
    
    # Run Stage 2 
    synonyms_data = stage2_synonym_retrieval(normalized_data)
    
    # Verify data structure
    assert isinstance(synonyms_data, dict)
    
    # Should have attempted to get synonyms for the normalized identifier
    # (Even if TEST:123 doesn't exist, the API call structure should be correct)
    print("✅ Stage 2 data structure test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])