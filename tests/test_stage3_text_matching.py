#!/usr/bin/env python3
"""
Test Stage 3: Text Matching & Lookup for FSH edge.
"""

import pytest
from phase1 import stage3_text_matching_and_lookup


def test_stage3_fsh_edge_text_matching():
    """Test Stage 3 text matching and lookup for FSH edge with expected results."""
    
    # Test edge with FSH and DLK1 entities
    edge = {
        'subject': 'GTOPDB:4386',
        'object': 'NCBIGene:8788', 
        'sentences': 'FSH stimulation increased DLK1 protein expression levels significantly.'
    }
    
    # Mock synonyms data from Stage 2 (what we expect from Stage 2 test)
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
    
    # Verify that synonyms found in text were looked up
    assert isinstance(lookup_cache, dict)
    
    # Should find "FSH" and "DLK1" in the text
    found_synonyms = set(lookup_cache.keys())
    expected_synonyms = {'FSH', 'DLK1'}
    
    # Check that the synonyms we expect were found
    for expected in expected_synonyms:
        assert expected in found_synonyms, f"Expected synonym '{expected}' not found in lookup cache"
    
    # Test FSH lookup results (filtered by SmallMolecule biolink type)
    fsh_results = lookup_cache['FSH']
    assert len(fsh_results) > 0, f"Expected some FSH results, got {len(fsh_results)}"
    
    # Verify FSH results contain the key expected entry (GTOPDB:4386 should be in there)
    actual_fsh_curies = [result['curie'] for result in fsh_results]
    assert 'GTOPDB:4386' in actual_fsh_curies, "Expected GTOPDB:4386 (original entity) in FSH results"
    
    # Verify FSH results are SmallMolecules
    for result in fsh_results:
        if 'types' in result:
            assert any('SmallMolecule' in t or 'Chemical' in t for t in result['types']), f"Expected SmallMolecule type for {result['curie']}"
    
    # Test DLK1 lookup results (filtered by Gene biolink type + human taxon)  
    dlk1_results = lookup_cache['DLK1']
    assert len(dlk1_results) > 0, f"Expected some DLK1 results, got {len(dlk1_results)}"
    
    # Verify DLK1 results contain key expected entries
    actual_dlk1_curies = [result['curie'] for result in dlk1_results]
    
    # With human taxon filtering (NCBITaxon:9606), should only get human DLK1
    # Since we're filtering by Gene type and human taxon, should get fewer results
    assert 'NCBIGene:8788' in actual_dlk1_curies, "Expected human DLK1 (NCBIGene:8788) in filtered results"
    
    # Verify all results are human genes (NCBITaxon:9606)
    for result in dlk1_results:
        if 'taxa' in result and result['taxa']:
            assert 'NCBITaxon:9606' in result['taxa'], f"Expected human taxon for {result['curie']}"
    
    # Human DLK1 should be in the results (likely top due to exact match)
    human_dlk1 = next((r for r in dlk1_results if r['curie'] == 'NCBIGene:8788'), None)
    assert human_dlk1 is not None, "Expected NCBIGene:8788 (human DLK1) in filtered results"
    assert human_dlk1['label'] == 'DLK1', "Expected human DLK1 label to be 'DLK1'"
    
    print("✅ Stage 3 text matching and lookup results:")
    print(f"   Found synonyms: {list(found_synonyms)}")
    for synonym in found_synonyms:
        result_count = len(lookup_cache[synonym]) if lookup_cache[synonym] else 0
        print(f"   '{synonym}' -> {result_count} lookup results")


def test_stage3_no_supporting_text():
    """Test Stage 3 with no supporting text."""
    
    # Edge with no sentences
    edge = {
        'subject': 'GTOPDB:4386',
        'object': 'NCBIGene:8788',
        'sentences': ''
    }
    
    synonyms_data = {
        'GTOPDB:4386': {'names': ['FSH']},
        'NCBIGene:8788': {'names': ['DLK1']}
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup(edge, synonyms_data)
    
    # Should return empty cache
    assert lookup_cache == {}
    
    print("✅ Stage 3 no text test passed")


def test_stage3_no_synonyms_found():
    """Test Stage 3 when no synonyms appear in text."""
    
    # Edge with text that doesn't contain entity synonyms
    edge = {
        'subject': 'GTOPDB:4386',
        'object': 'NCBIGene:8788',
        'sentences': 'The experiment showed interesting results with compound X and protein Y.'
    }
    
    synonyms_data = {
        'GTOPDB:4386': {'names': ['FSH']},
        'NCBIGene:8788': {'names': ['DLK1']}
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup(edge, synonyms_data)
    
    # Should return empty cache
    assert lookup_cache == {}
    
    print("✅ Stage 3 no synonyms found test passed")


def test_stage3_case_insensitive_matching():
    """Test Stage 3 case-insensitive synonym matching."""
    
    # Edge with mixed case text
    edge = {
        'subject': 'GTOPDB:4386',
        'object': 'NCBIGene:8788',
        'sentences': 'fsh stimulation increased dlk1 expression.'  # lowercase
    }
    
    synonyms_data = {
        'GTOPDB:4386': {'names': ['FSH']},  # uppercase
        'NCBIGene:8788': {'names': ['DLK1']}  # uppercase
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup(edge, synonyms_data)
    
    # Should find both synonyms despite case differences
    found_synonyms = set(lookup_cache.keys())
    expected_synonyms = {'FSH', 'DLK1'}
    
    for expected in expected_synonyms:
        assert expected in found_synonyms, f"Case-insensitive match failed for '{expected}'"
    
    print("✅ Stage 3 case-insensitive matching test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])