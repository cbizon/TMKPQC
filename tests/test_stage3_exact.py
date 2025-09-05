#!/usr/bin/env python3
"""
Test Stage 3: Text Matching & Lookup with exact expected input/output.
"""

import pytest
from phase1 import stage3_text_matching_and_lookup


def test_stage3_fsh_edge_exact_matches():
    """Test Stage 3 with exact expected input and output for perfect matches only."""
    
    # EXACT INPUT as defined
    edge = {
        'subject': 'GTOPDB:4386',
        'object': 'NCBIGene:8788', 
        'sentences': 'FSH stimulation increased DLK1 protein expression levels significantly.'
    }
    
    synonyms_data = {
        'GTOPDB:4386': {
            'curie': 'GTOPDB:4386',
            'preferred_name': 'FSH',
            'names': ['FSH', '4384', '4377'],
            'types': ['SmallMolecule']
        },
        'NCBIGene:8788': {
            'curie': 'NCBIGene:8788',
            'preferred_name': 'DLK1',
            'names': ['DLK1', 'FA1', 'PREF1', 'fetal antigen 1', 'protein delta homolog 1'],
            'types': ['Gene']
        }
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup(edge, synonyms_data)
    
    # EXACT OUTPUT VERIFICATION
    assert isinstance(lookup_cache, dict)
    assert set(lookup_cache.keys()) == {'FSH', 'DLK1'}, f"Expected FSH and DLK1 keys, got {set(lookup_cache.keys())}"
    
    # FSH: Should have exactly 3 perfect matches with SmallMolecule type
    fsh_results = lookup_cache['FSH']
    assert len(fsh_results) == 3, f"Expected exactly 3 FSH perfect matches, got {len(fsh_results)}"
    
    expected_fsh_curies = {'CHEBI:81569', 'GTOPDB:4386', 'GTOPDB:4387'}
    actual_fsh_curies = {result['curie'] for result in fsh_results}
    assert actual_fsh_curies == expected_fsh_curies, f"Expected FSH CURIEs {expected_fsh_curies}, got {actual_fsh_curies}"
    
    # Verify each FSH result has exact 'FSH' synonym
    for result in fsh_results:
        synonyms = result.get('synonyms', [])
        has_exact_fsh = 'FSH' in synonyms
        assert has_exact_fsh, f"Result {result['curie']} missing exact 'FSH' synonym: {synonyms}"
    
    # DLK1: Should have exactly 1 perfect match with Gene type + human taxon
    dlk1_results = lookup_cache['DLK1']
    assert len(dlk1_results) == 1, f"Expected exactly 1 DLK1 perfect match, got {len(dlk1_results)}"
    
    dlk1_result = dlk1_results[0]
    assert dlk1_result['curie'] == 'NCBIGene:8788', f"Expected NCBIGene:8788, got {dlk1_result['curie']}"
    assert dlk1_result['label'] == 'DLK1', f"Expected label 'DLK1', got {dlk1_result['label']}"
    assert 'NCBITaxon:9606' in dlk1_result.get('taxa', []), "Expected human taxon in DLK1 result"
    
    # Verify DLK1 result has exact 'DLK1' synonym
    dlk1_synonyms = dlk1_result.get('synonyms', [])
    has_exact_dlk1 = 'DLK1' in dlk1_synonyms
    assert has_exact_dlk1, f"DLK1 result missing exact 'DLK1' synonym: {dlk1_synonyms}"
    
    print("✅ Stage 3 perfect match results:")
    print(f"   FSH: {len(fsh_results)} perfect matches")
    print(f"   DLK1: {len(dlk1_results)} perfect matches")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])