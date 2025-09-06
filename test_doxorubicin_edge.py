#!/usr/bin/env python3
"""
Test for doxorubicin edge classification.

This edge is currently being classified as "ambiguous" but should be "good".
"""

import json
import pytest
from phase1 import stage1_entity_collection_and_normalization, stage2_synonym_retrieval, stage3_text_matching_and_lookup, stage4_classification_logic


def test_doxorubicin_xrcc1_edge_should_be_good():
    """Test that the doxorubicin -> XRCC1 edge should be classified as good, not ambiguous."""
    
    # The actual edge data from the pipeline
    edge = {
        "subject": "CHEBI:28748",
        "predicate": "biolink:affects", 
        "object": "UniProtKB:P18887",
        "primary_knowledge_source": "infores:text-mining-provider-targeted",
        "publications": ["PMID:28258155", "PMID:34783124", "PMID:29929045"],
        "biolink:tmkp_confidence_score": 0.9983171550000001,
        "sentences": "The significant increase in CDKN1A and XRCC1 suggest a cell cycle arrest and implies an alternative NHEJ pathway in response to doxorubicin-induced DNA breaks.|NA|However, FANCD2, BRCA1 and XRCC1 foci, prominently associated with 53BP1 foci and hence DSBs resolved by cNHEJ, were only detected in doxorubicin-treated XRCC4-deficient cells.|NA",
        "tmkp_ids": ["tmkp:ae3877b6ed48c7afbc0991e8578f84513dd12cacb2bb6a485df182d33d4d4e7f"],
        "knowledge_level": "not_provided",
        "agent_type": "text_mining_agent", 
        "qualified_predicate": "biolink:causes",
        "object_aspect_qualifier": "activity_or_abundance",
        "object_direction_qualifier": "increased"
    }
    
    # Create a temporary edge file for testing
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps(edge) + '\n')
        edge_file = f.name
    
    try:
        # Run the 4-stage pipeline on this single edge
        print("\n=== Running 4-stage pipeline on doxorubicin edge ===")
        
        # Stage 1: Entity collection and normalization
        entities, normalized_data = stage1_entity_collection_and_normalization(edge_file)
        print(f"Stage 1: Found {len(entities)} entities")
        
        # Stage 2: Synonym retrieval  
        synonyms_data = stage2_synonym_retrieval(normalized_data)
        print(f"Stage 2: Retrieved synonyms for {len(synonyms_data)} entities")
        
        # Stage 3: Text matching and lookup
        lookup_cache = stage3_text_matching_and_lookup(edge, synonyms_data)
        print(f"Stage 3: Found {len(lookup_cache)} synonyms in text")
        
        # Stage 4: Classification
        classification, debug_info = stage4_classification_logic(edge, lookup_cache, normalized_data, synonyms_data)
        
        print(f"\nClassification result: {classification}")
        print(f"Reason: {debug_info.get('reason', 'N/A')}")
        print(f"Subject synonyms found: {debug_info.get('subject_synonyms_found', [])}")
        print(f"Object synonyms found: {debug_info.get('object_synonyms_found', [])}")
        print(f"Subject ambiguous: {debug_info.get('subject_ambiguous', False)}")
        print(f"Object ambiguous: {debug_info.get('object_ambiguous', False)}")
        
        # The test assertion - this edge should be classified as "good"
        assert classification == "good", f"Expected 'good' but got '{classification}'. Reason: {debug_info.get('reason')}"
        
    finally:
        # Clean up temporary file
        os.unlink(edge_file)


if __name__ == "__main__":
    test_doxorubicin_xrcc1_edge_should_be_good()