#!/usr/bin/env python3
"""
Comprehensive tests for Stage 4 preferred label logic.

Tests all cases:
1. Multiple preferred labels -> ambiguous
2a. One preferred label (matches input) -> good  
2b. One preferred label (doesn't match input) -> bad
3. No preferred, one regular synonym -> good if matches input, bad otherwise
4. No preferred, multiple regular synonyms -> ambiguous
"""

import json
import pytest
from phase1 import get_winning_entity_for_synonym, classify_edge


class TestPreferredLabelLogic:
    """Test the preferred label hierarchy logic."""
    
    def test_case_1_multiple_preferred_labels_ambiguous(self):
        """Case 1: Multiple entities have the synonym as preferred label -> ambiguous"""
        
        # Create lookup results where multiple entities have "insulin" as their preferred label
        lookup_results = [
            {'curie': 'CHEBI:5931', 'label': 'insulin', 'synonyms': ['insulin hormone'], 'score': 100},
            {'curie': 'UNII:12345', 'label': 'insulin', 'synonyms': ['insulin drug'], 'score': 90},
        ]
        
        winning_entity = get_winning_entity_for_synonym("insulin", lookup_results)
        assert winning_entity is None, "Multiple preferred labels should return None (ambiguous)"
    
    def test_case_2a_one_preferred_matches_input_good(self):
        """Case 2a: One preferred label, matches normalized input -> good"""
        
        edge = {
            "subject": "CHEBI:5931",
            "object": "NCBIGene:3479", 
            "sentences": "Insulin increases IGF1 expression in liver cells."
        }
        
        # Mock lookup cache - insulin has one preferred label
        lookup_cache = {
            "insulin": [
                {'curie': 'CHEBI:5931', 'label': 'insulin', 'synonyms': ['insulin hormone'], 'score': 100},
                {'curie': 'UNII:12345', 'label': 'hormone', 'synonyms': ['insulin', 'growth hormone'], 'score': 80}
            ],
            "IGF1": [
                {'curie': 'NCBIGene:3479', 'label': 'IGF1', 'synonyms': ['IGF1', 'insulin-like growth factor'], 'score': 100}
            ]
        }
        
        # Mock normalized data
        normalized_data = {
            "CHEBI:5931": {"id": {"identifier": "CHEBI:5931"}},
            "NCBIGene:3479": {"id": {"identifier": "NCBIGene:3479"}}
        }
        
        # Mock synonyms data  
        synonyms_data = {
            "CHEBI:5931": {"names": ["insulin"]},
            "NCBIGene:3479": {"names": ["IGF1"]}
        }
        
        classification, debug_info = classify_edge(edge, lookup_cache, normalized_data, synonyms_data)
        assert classification == "good", f"Expected 'good' but got '{classification}'. Reason: {debug_info.get('reason')}"
    
    def test_case_2b_one_preferred_wrong_entity_bad(self):
        """Case 2b: One preferred label, doesn't match normalized input -> bad"""
        
        edge = {
            "subject": "CHEBI:5931",  # Expected insulin
            "object": "NCBIGene:3479",
            "sentences": "Insulin increases IGF1 expression in liver cells."
        }
        
        # Mock lookup cache - insulin resolves to different entity than expected
        lookup_cache = {
            "insulin": [
                {'curie': 'UNII:DIFFERENT', 'label': 'insulin', 'synonyms': ['insulin hormone'], 'score': 100},  # Wrong entity!
                {'curie': 'CHEBI:5931', 'label': 'hormone', 'synonyms': ['insulin', 'growth hormone'], 'score': 80}
            ],
            "IGF1": [
                {'curie': 'NCBIGene:3479', 'label': 'IGF1', 'synonyms': ['IGF1'], 'score': 100}
            ]
        }
        
        normalized_data = {
            "CHEBI:5931": {"id": {"identifier": "CHEBI:5931"}},
            "NCBIGene:3479": {"id": {"identifier": "NCBIGene:3479"}}
        }
        
        synonyms_data = {
            "CHEBI:5931": {"names": ["insulin"]},
            "NCBIGene:3479": {"names": ["IGF1"]}
        }
        
        classification, debug_info = classify_edge(edge, lookup_cache, normalized_data, synonyms_data)
        assert classification == "bad", f"Expected 'bad' but got '{classification}'. Reason: {debug_info.get('reason')}"
        assert "resolves to UNII:DIFFERENT but expected CHEBI:5931" in debug_info.get('reason', '')
    
    def test_case_3_no_preferred_one_regular_good(self):
        """Case 3: No preferred labels, one regular synonym -> good"""
        
        edge = {
            "subject": "CHEBI:5931",
            "object": "NCBIGene:3479",
            "sentences": "Insulin increases IGF1 expression."
        }
        
        # Mock lookup cache - no preferred labels, only one regular synonym
        lookup_cache = {
            "insulin": [
                {'curie': 'CHEBI:5931', 'label': 'hormone', 'synonyms': ['insulin', 'growth hormone'], 'score': 100}
            ],
            "IGF1": [
                {'curie': 'NCBIGene:3479', 'label': 'IGF1', 'synonyms': ['IGF1'], 'score': 100}
            ]
        }
        
        normalized_data = {
            "CHEBI:5931": {"id": {"identifier": "CHEBI:5931"}},
            "NCBIGene:3479": {"id": {"identifier": "NCBIGene:3479"}}
        }
        
        synonyms_data = {
            "CHEBI:5931": {"names": ["insulin"]},
            "NCBIGene:3479": {"names": ["IGF1"]}
        }
        
        classification, debug_info = classify_edge(edge, lookup_cache, normalized_data, synonyms_data)
        assert classification == "good", f"Expected 'good' but got '{classification}'. Reason: {debug_info.get('reason')}"
    
    def test_case_4_no_preferred_multiple_regular_ambiguous(self):
        """Case 4: No preferred labels, multiple regular synonyms -> ambiguous"""
        
        edge = {
            "subject": "CHEBI:5931",
            "object": "NCBIGene:3479",
            "sentences": "Insulin increases IGF1 expression."
        }
        
        # Mock lookup cache - no preferred labels, multiple regular synonyms
        lookup_cache = {
            "insulin": [
                {'curie': 'CHEBI:5931', 'label': 'hormone1', 'synonyms': ['insulin', 'growth hormone'], 'score': 100},
                {'curie': 'UNII:12345', 'label': 'hormone2', 'synonyms': ['insulin', 'other hormone'], 'score': 90}
            ],
            "IGF1": [
                {'curie': 'NCBIGene:3479', 'label': 'IGF1', 'synonyms': ['IGF1'], 'score': 100}
            ]
        }
        
        normalized_data = {
            "CHEBI:5931": {"id": {"identifier": "CHEBI:5931"}},
            "NCBIGene:3479": {"id": {"identifier": "NCBIGene:3479"}}
        }
        
        synonyms_data = {
            "CHEBI:5931": {"names": ["insulin"]},
            "NCBIGene:3479": {"names": ["IGF1"]}
        }
        
        classification, debug_info = classify_edge(edge, lookup_cache, normalized_data, synonyms_data)
        assert classification == "ambiguous", f"Expected 'ambiguous' but got '{classification}'. Reason: {debug_info.get('reason')}"
        assert "Multiple entities have \"insulin\" as regular synonym (no preferred label)" in debug_info.get('reason', '')
    
    def test_winning_entity_helper_function(self):
        """Test the get_winning_entity_for_synonym helper function directly."""
        
        # Case 1: Multiple preferred labels -> None
        results = [
            {'curie': 'A', 'label': 'test', 'synonyms': [], 'score': 100},
            {'curie': 'B', 'label': 'test', 'synonyms': [], 'score': 90}
        ]
        assert get_winning_entity_for_synonym("test", results) is None
        
        # Case 2: One preferred label -> that entity
        results = [
            {'curie': 'A', 'label': 'test', 'synonyms': [], 'score': 100},
            {'curie': 'B', 'label': 'other', 'synonyms': ['test'], 'score': 90}
        ]
        winner = get_winning_entity_for_synonym("test", results)
        assert winner['curie'] == 'A'
        
        # Case 3: No preferred, one regular -> that entity
        results = [
            {'curie': 'A', 'label': 'other1', 'synonyms': ['test'], 'score': 100}
        ]
        winner = get_winning_entity_for_synonym("test", results)
        assert winner['curie'] == 'A'
        
        # Case 4: No preferred, multiple regular -> None
        results = [
            {'curie': 'A', 'label': 'other1', 'synonyms': ['test'], 'score': 100},
            {'curie': 'B', 'label': 'other2', 'synonyms': ['test'], 'score': 90}
        ]
        assert get_winning_entity_for_synonym("test", results) is None
    
    def test_case_insensitive_matching(self):
        """Test that preferred label matching is case-insensitive."""
        
        # Mixed case should still match as preferred
        results = [
            {'curie': 'A', 'label': 'Insulin', 'synonyms': [], 'score': 100},
            {'curie': 'B', 'label': 'hormone', 'synonyms': ['insulin'], 'score': 90}
        ]
        winner = get_winning_entity_for_synonym("insulin", results)  # lowercase query
        assert winner['curie'] == 'A', "Case-insensitive preferred label match should win"
    
    def test_mixed_case_scenarios(self):
        """Test various mixed case scenarios."""
        
        # Test with different case variations
        test_cases = [
            ("INSULIN", "insulin"),  # uppercase synonym, lowercase label
            ("insulin", "INSULIN"),  # lowercase synonym, uppercase label  
            ("Insulin", "insulin"),  # title case synonym, lowercase label
            ("insulin", "Insulin"),  # lowercase synonym, title case label
        ]
        
        for synonym, label in test_cases:
            results = [
                {'curie': 'A', 'label': label, 'synonyms': [], 'score': 100},
                {'curie': 'B', 'label': 'other', 'synonyms': [synonym], 'score': 90}
            ]
            winner = get_winning_entity_for_synonym(synonym, results)
            assert winner['curie'] == 'A', f"Case-insensitive match failed for synonym='{synonym}', label='{label}'"
    
    def test_doxorubicin_real_world_case(self):
        """Test the actual doxorubicin case that motivated this logic."""
        
        edge = {
            "subject": "CHEBI:28748",
            "object": "UniProtKB:P18887", 
            "sentences": "Doxorubicin increases XRCC1 expression."
        }
        
        # Simulate the real doxorubicin lookup scenario
        lookup_cache = {
            "doxorubicin": [
                # One has doxorubicin as preferred label (should win)
                {'curie': 'CHEBI:28748', 'label': 'Doxorubicin', 'synonyms': ['DOX', 'adriamycin'], 'score': 100},
                # Others have it as regular synonym only
                {'curie': 'CHEBI:64816', 'label': 'doxorubicin(1+)', 'synonyms': ['doxorubicin', 'dox cation'], 'score': 80}
            ],
            "XRCC1": [
                {'curie': 'NCBIGene:7515', 'label': 'XRCC1', 'synonyms': ['XRCC1', 'DNA repair'], 'score': 100}
            ]
        }
        
        normalized_data = {
            "CHEBI:28748": {"id": {"identifier": "CHEBI:28748"}},
            "UniProtKB:P18887": {"id": {"identifier": "NCBIGene:7515"}}  # Normalized to gene
        }
        
        synonyms_data = {
            "CHEBI:28748": {"names": ["doxorubicin"]},
            "NCBIGene:7515": {"names": ["XRCC1"]}
        }
        
        classification, debug_info = classify_edge(edge, lookup_cache, normalized_data, synonyms_data)
        assert classification == "good", f"Doxorubicin case should be 'good' with preferred label logic. Got '{classification}'. Reason: {debug_info.get('reason')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])