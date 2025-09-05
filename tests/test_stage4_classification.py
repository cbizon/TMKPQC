#!/usr/bin/env python3
"""
Test Stage 4: Classification Logic with exact expected input/output.
"""

import pytest
from phase1 import stage4_classification_logic


def test_stage4_fsh_edge_classification():
    """Test Stage 4 classification for FSH edge - should be AMBIGUOUS due to multiple matches."""
    
    # Test edge with FSH and DLK1 entities
    edge = {
        'subject': 'GTOPDB:4386',
        'object': 'NCBIGene:8788', 
        'sentences': 'FSH stimulation increased DLK1 protein expression levels significantly.'
    }
    
    # Lookup cache from Stage 3 (exact results we validated)
    lookup_cache = {
        'FSH': [
            {
                'curie': 'CHEBI:81569',
                'label': 'FSH',
                'synonyms': ['FSH', 'follicle-stimulating hormone'],
                'types': ['SmallMolecule']
            },
            {
                'curie': 'GTOPDB:4386', 
                'label': 'FSH',
                'synonyms': ['FSH', '4384', '4377'],
                'types': ['SmallMolecule']
            },
            {
                'curie': 'GTOPDB:4387',
                'label': 'FSH',
                'synonyms': ['FSH', 'follicle stimulating hormone'],
                'types': ['SmallMolecule'] 
            }
        ],
        'DLK1': [
            {
                'curie': 'NCBIGene:8788',
                'label': 'DLK1',
                'synonyms': ['DLK1', 'FA1', 'PREF1', 'fetal antigen 1', 'protein delta homolog 1'],
                'types': ['Gene'],
                'taxa': ['NCBITaxon:9606']
            }
        ]
    }
    
    # Normalized data from Stage 1
    normalized_data = {
        'GTOPDB:4386': {
            'id': {'identifier': 'GTOPDB:4386', 'label': 'FSH'},
            'equivalent_identifiers': [
                {'identifier': 'GTOPDB:4386', 'label': 'FSH'},
                {'identifier': 'CHEBI:81569', 'label': 'follicle-stimulating hormone'}
            ],
            'type': ['biolink:SmallMolecule']
        },
        'NCBIGene:8788': {
            'id': {'identifier': 'NCBIGene:8788', 'label': 'DLK1'},
            'equivalent_identifiers': [
                {'identifier': 'NCBIGene:8788', 'label': 'DLK1'}
            ],
            'type': ['biolink:Gene']
        }
    }
    
    # Synonyms data from Stage 2
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
    
    # Run Stage 4
    classification, debug_info = stage4_classification_logic(
        edge, lookup_cache, normalized_data, synonyms_data
    )
    
    # EXPECTED RESULTS:
    # FSH: Multiple matches (CHEBI:81569, GTOPDB:4386, GTOPDB:4387) = AMBIGUOUS
    # DLK1: Single match (NCBIGene:8788) that equals original = GOOD
    # Overall edge classification should be AMBIGUOUS (due to FSH ambiguity)
    
    print(f"✅ Stage 4 classification result: {classification}")
    print(f"   Debug info: {debug_info}")
    
    # Verify classification is AMBIGUOUS due to FSH having multiple possible entities
    assert classification == 'ambiguous', f"Expected 'ambiguous', got '{classification}'"
    
    # Verify debug info contains expected details
    assert debug_info['subject_curie'] == 'GTOPDB:4386'
    assert debug_info['object_curie'] == 'NCBIGene:8788'
    assert 'FSH stimulation increased DLK1' in debug_info['edge_text']


def test_stage4_unambiguous_case():
    """Test Stage 4 with a hypothetical case where both entities have single matches."""
    
    # Edge with unique synonyms that don't create ambiguity
    edge = {
        'subject': 'NCBIGene:8788',
        'object': 'NCBIGene:8788', 
        'sentences': 'DLK1 protein expression increased significantly.'
    }
    
    # Lookup cache with only single matches
    lookup_cache = {
        'DLK1': [
            {
                'curie': 'NCBIGene:8788',
                'label': 'DLK1',
                'synonyms': ['DLK1', 'FA1', 'PREF1'],
                'types': ['Gene'],
                'taxa': ['NCBITaxon:9606']
            }
        ]
    }
    
    normalized_data = {
        'NCBIGene:8788': {
            'id': {'identifier': 'NCBIGene:8788', 'label': 'DLK1'},
            'equivalent_identifiers': [
                {'identifier': 'NCBIGene:8788', 'label': 'DLK1'}
            ],
            'type': ['biolink:Gene']
        }
    }
    
    synonyms_data = {
        'NCBIGene:8788': {
            'curie': 'NCBIGene:8788',
            'preferred_name': 'DLK1',
            'names': ['DLK1', 'FA1', 'PREF1'],
            'types': ['Gene']
        }
    }
    
    # Run Stage 4
    classification, debug_info = stage4_classification_logic(
        edge, lookup_cache, normalized_data, synonyms_data
    )
    
    print(f"✅ Unambiguous case classification: {classification}")
    
    # Should be GOOD since DLK1 has only one match that equals the original entity
    assert classification == 'good', f"Expected 'good', got '{classification}'"


def test_stage4_no_synonyms_in_text():
    """Test Stage 4 when no entity synonyms are found in text - should be BAD."""
    
    edge = {
        'subject': 'GTOPDB:4386',
        'object': 'NCBIGene:8788',
        'sentences': 'Compound X increased protein Y expression levels.'  # No FSH or DLK1
    }
    
    # Empty lookup cache (no synonyms found in text)
    lookup_cache = {}
    
    normalized_data = {
        'GTOPDB:4386': {'id': {'identifier': 'GTOPDB:4386', 'label': 'FSH'}},
        'NCBIGene:8788': {'id': {'identifier': 'NCBIGene:8788', 'label': 'DLK1'}}
    }
    
    synonyms_data = {
        'GTOPDB:4386': {'names': ['FSH'], 'types': ['SmallMolecule']},
        'NCBIGene:8788': {'names': ['DLK1'], 'types': ['Gene']}
    }
    
    # Run Stage 4
    classification, debug_info = stage4_classification_logic(
        edge, lookup_cache, normalized_data, synonyms_data
    )
    
    print(f"✅ No synonyms in text classification: {classification}")
    
    # Should be BAD since no entity synonyms were found in the supporting text
    assert classification == 'bad', f"Expected 'bad', got '{classification}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])