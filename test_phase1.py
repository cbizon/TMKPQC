"""
Tests for phase1.py

These tests cover the edge classification logic including entity collection,
normalization, synonym matching, and edge classification.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from phase1 import EdgeClassifier


class TestEdgeClassifier:
    """Tests for EdgeClassifier class."""
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary test files."""
        # Create temporary edges file
        edges_data = [
            {
                "subject": "CHEBI:28748",
                "object": "UniProtKB:P18887", 
                "predicate": "biolink:affects",
                "sentences": "Doxorubicin increases XRCC1 expression in cells."
            },
            {
                "subject": "CHEBI:28748",
                "object": "UniProtKB:P99999",
                "predicate": "biolink:affects", 
                "sentences": ""
            }
        ]
        
        # Create temporary nodes file
        nodes_data = [
            {
                "id": "CHEBI:28748",
                "name": "doxorubicin",
                "category": ["biolink:SmallMolecule"]
            },
            {
                "id": "UniProtKB:P18887",
                "name": "XRCC1_HUMAN",
                "category": ["biolink:Protein"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write edges file
            edges_file = temp_path / "test_edges.jsonl"
            with open(edges_file, 'w') as f:
                for edge in edges_data:
                    f.write(json.dumps(edge) + '\n')
            
            # Write nodes file
            nodes_file = temp_path / "test_nodes.jsonl"
            with open(nodes_file, 'w') as f:
                for node in nodes_data:
                    f.write(json.dumps(node) + '\n')
            
            output_dir = temp_path / "output"
            
            yield str(edges_file), str(nodes_file), str(output_dir)
    
    
    def test_find_synonyms_in_text(self, temp_files):
        """Test finding synonyms in text."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        text = "Doxorubicin increases XRCC1 expression in cells."
        synonyms = ["doxorubicin", "XRCC1", "adriamycin", "notfound"]
        
        found = classifier.find_synonyms_in_text(text, synonyms)
        
        # Should find case-insensitive matches
        assert "doxorubicin" in found
        assert "XRCC1" in found
        assert "notfound" not in found
    
    def test_find_synonyms_word_boundaries(self, temp_files):
        """Test that synonym matching respects word boundaries."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        text = "The protein kinase activity was measured."
        synonyms = ["protein", "kinase", "tein"]  # "tein" should not match "protein"
        
        found = classifier.find_synonyms_in_text(text, synonyms)
        
        assert "protein" in found
        assert "kinase" in found
        assert "tein" not in found  # Partial match should not be found
    
    
    
    def test_write_edge_result(self, temp_files):
        """Test writing edge results to output files."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        edge = {
            "subject": "CHEBI:28748",
            "object": "UniProtKB:P18887",
            "sentences": "Test sentence"
        }
        
        classifier.write_edge_result(edge, "good")
        
        # Check that file was created and contains correct data
        good_file = Path(output_dir) / "good_edges.jsonl"
        assert good_file.exists()
        
        with open(good_file, 'r') as f:
            written_edge = json.loads(f.read().strip())
        
        assert written_edge["subject"] == "CHEBI:28748"
        assert written_edge["qc_classification"] == "good"
        assert written_edge["qc_phase"] == "phase1_entity_identification"
    


class TestEdgeClassifierIntegration:
    """Integration tests for EdgeClassifier."""
    
    @patch('phase1.batch_get_normalized_nodes')
    @patch('phase1.batch_get_synonyms') 
    @patch('phase1.lookup_names')
    def test_full_run_small_dataset(self, mock_lookup, mock_synonyms, mock_normalize, tmp_path):
        """Test full run with mocked API calls."""
        # Create temporary test data
        edges_data = [
            {
                "subject": "CHEBI:28748",
                "object": "UniProtKB:P18887", 
                "predicate": "biolink:affects",
                "sentences": "Doxorubicin increases XRCC1 expression in cells."
            }
        ]
        
        nodes_data = [
            {
                "id": "CHEBI:28748",
                "name": "doxorubicin",
                "category": ["biolink:SmallMolecule"]
            },
            {
                "id": "UniProtKB:P18887",
                "name": "XRCC1_HUMAN",
                "category": ["biolink:Protein"]
            }
        ]
        
        # Write test files
        edges_file = tmp_path / "test_edges.jsonl"
        nodes_file = tmp_path / "test_nodes.jsonl"
        output_dir = tmp_path / "output"
        
        with open(edges_file, 'w') as f:
            for edge in edges_data:
                f.write(json.dumps(edge) + '\n')
        
        with open(nodes_file, 'w') as f:
            for node in nodes_data:
                f.write(json.dumps(node) + '\n')
        
        # Mock API responses
        mock_normalize.return_value = {
            "CHEBI:28748": {
                "id": {"identifier": "CHEBI:28748"},
                "type": ["biolink:SmallMolecule"]
            },
            "UniProtKB:P18887": {
                "id": {"identifier": "UniProtKB:P18887"},
                "type": ["biolink:Protein"]
            },
            "UniProtKB:P99999": {
                "id": {"identifier": "UniProtKB:P99999"},
                "type": ["biolink:Protein"]
            }
        }
        
        mock_synonyms.return_value = {
            "CHEBI:28748": {"names": ["doxorubicin", "Doxorubicin", "adriamycin"]},
            "UniProtKB:P18887": {"names": ["XRCC1", "XRCC1_HUMAN"]},
            "UniProtKB:P99999": {"names": ["TEST_PROTEIN"]}
        }
        
        # Mock lookup to return single matches (not ambiguous)
        mock_lookup.return_value = [{"curie": "CHEBI:28748", "score": 100, "label": "doxorubicin"}]
        
        classifier = EdgeClassifier(str(edges_file), str(nodes_file), str(output_dir))
        classifier.run_streaming(max_edges=1)
        
        # Check that output directory was created and good edges file exists
        output_path = Path(output_dir)
        assert output_path.exists()
        assert (output_path / "good_edges.jsonl").exists()
        
        # Read the good edge to verify it was classified correctly
        with open(output_path / "good_edges.jsonl", 'r') as f:
            good_edge = json.loads(f.read().strip())
            assert good_edge["qc_classification"] == "good"
            assert good_edge["subject"] == "CHEBI:28748"
        
        # Verify API calls were made
        mock_normalize.assert_called_once()
        mock_synonyms.assert_called_once()
    
    
    @patch('phase1.bulk_lookup_names')
    @patch('phase1.batch_get_synonyms')
    @patch('phase1.batch_get_normalized_nodes')
    def test_streaming_classify_edge(self, mock_normalize, mock_synonyms, mock_bulk_lookup, tmp_path):
        """Test classify_edge method that was causing the bug"""
        # Setup test data
        normalized_data = {
            'CHEBI:28748': {'id': {'identifier': 'CHEBI:28748'}},
            'UniProtKB:P18887': {'id': {'identifier': 'UniProtKB:P18887'}}
        }
        
        synonyms_data = {
            'CHEBI:28748': {'names': ['doxorubicin', 'adriamycin']},
            'UniProtKB:P18887': {'names': ['XRCC1', 'X-ray repair cross-complementing protein 1']}
        }
        
        lookup_cache = {
            'doxorubicin': [{'curie': 'CHEBI:28748', 'label': 'doxorubicin', 'score': 1.0}],
            'XRCC1': [{'curie': 'UniProtKB:P18887', 'label': 'XRCC1', 'score': 1.0}]
        }
        
        # Create temporary files
        edges_file = tmp_path / "test_edges.jsonl"
        nodes_file = tmp_path / "test_nodes.jsonl"
        output_dir = tmp_path / "output"
        
        edge = {
            'subject': 'CHEBI:28748',
            'object': 'UniProtKB:P18887',
            'sentences': 'doxorubicin treatment increases XRCC1 levels'
        }
        
        with open(edges_file, 'w') as f:
            json.dump(edge, f)
        
        with open(nodes_file, 'w') as f:
            json.dump({'id': 'CHEBI:28748'}, f)
            f.write('\n')
            json.dump({'id': 'UniProtKB:P18887'}, f)
        
        classifier = EdgeClassifier(str(edges_file), str(nodes_file), str(output_dir))
        
        # Test the method that was buggy
        classification, debug_info = classifier.classify_edge(
            edge, lookup_cache, normalized_data, synonyms_data
        )
        
        # This should be 'good', not 'bad' (the bug was returning 'bad' due to missing synonyms)
        assert classification == 'good'
        assert 'doxorubicin' in debug_info.get('subject_synonyms_found', [])
        assert 'XRCC1' in debug_info.get('object_synonyms_found', [])

    @patch('phase1.bulk_lookup_names')
    @patch('phase1.batch_get_synonyms') 
    @patch('phase1.batch_get_normalized_nodes')
    def test_streaming_missing_synonyms_bug_regression(self, mock_normalize, mock_synonyms, mock_bulk_lookup, tmp_path):
        """Regression test for the bug where all edges were classified as 'bad' due to incorrect synonym lookup"""
        # This test ensures we don't regress back to the bug where synonyms were looked up 
        # using original CURIEs instead of preferred/normalized CURIEs
        
        normalized_data = {
            'ORIGINAL:123': {'id': {'identifier': 'PREFERRED:456'}},  # Original maps to different preferred
            'ORIGINAL:789': {'id': {'identifier': 'PREFERRED:101'}}
        }
        
        # Synonyms are stored by PREFERRED CURIEs, not original ones
        synonyms_data = {
            'PREFERRED:456': {'names': ['test_compound']},
            'PREFERRED:101': {'names': ['test_protein']}
        }
        
        lookup_cache = {
            'test_compound': [{'curie': 'PREFERRED:456', 'label': 'test_compound', 'score': 1.0}],
            'test_protein': [{'curie': 'PREFERRED:101', 'label': 'test_protein', 'score': 1.0}]
        }
        
        # Create temporary files
        edges_file = tmp_path / "test_edges.jsonl"
        nodes_file = tmp_path / "test_nodes.jsonl"
        output_dir = tmp_path / "output"
        
        edge = {
            'subject': 'ORIGINAL:123',  # Original CURIE, not preferred
            'object': 'ORIGINAL:789',   # Original CURIE, not preferred
            'sentences': 'test_compound affects test_protein levels'
        }
        
        with open(edges_file, 'w') as f:
            json.dump(edge, f)
        
        with open(nodes_file, 'w') as f:
            json.dump({'id': 'ORIGINAL:123'}, f)
            f.write('\n')
            json.dump({'id': 'ORIGINAL:789'}, f)
        
        classifier = EdgeClassifier(str(edges_file), str(nodes_file), str(output_dir))
        
        # The buggy version would look for synonyms under 'ORIGINAL:123' and 'ORIGINAL:789'
        # which don't exist in synonyms_data, causing "Missing synonyms" error
        # The fixed version should look under 'PREFERRED:456' and 'PREFERRED:101'
        classification, debug_info = classifier.classify_edge(
            edge, lookup_cache, normalized_data, synonyms_data
        )
        
        # Should be 'good', not 'bad' (the bug would return 'bad' with "Missing synonyms")
        assert classification == 'good'
        assert debug_info.get('reason') != 'Missing synonyms for subject or object'
        assert 'test_compound' in debug_info.get('subject_synonyms_found', [])
        assert 'test_protein' in debug_info.get('object_synonyms_found', [])

    @patch('phase1.bulk_lookup_names')
    @patch('phase1.batch_get_synonyms')
    @patch('phase1.batch_get_normalized_nodes')
    def test_streaming_workflow_integration(self, mock_normalize, mock_synonyms, mock_bulk_lookup, tmp_path):
        """Integration test for streaming workflow to catch similar bugs"""
        mock_normalize.return_value = {
            'CHEBI:28748': {'id': {'identifier': 'CHEBI:28748'}},
            'UniProtKB:P18887': {'id': {'identifier': 'UniProtKB:P18887'}}
        }
        
        mock_synonyms.return_value = {
            'CHEBI:28748': {'names': ['doxorubicin', 'adriamycin']},
            'UniProtKB:P18887': {'names': ['XRCC1']}
        }
        
        mock_bulk_lookup.return_value = {
            'doxorubicin': [{'curie': 'CHEBI:28748', 'label': 'doxorubicin', 'score': 1.0}],
            'XRCC1': [{'curie': 'UniProtKB:P18887', 'label': 'XRCC1', 'score': 1.0}]
        }
        
        # Create test files
        edges_file = tmp_path / "test_edges.jsonl"
        nodes_file = tmp_path / "test_nodes.jsonl"
        output_dir = tmp_path / "output"
        
        edges = [
            {
                'subject': 'CHEBI:28748',
                'object': 'UniProtKB:P18887',
                'sentences': 'doxorubicin treatment affects XRCC1 protein levels'
            },
            {
                'subject': 'CHEBI:28748', 
                'object': 'UniProtKB:P18887',
                'sentences': 'some unrelated text without entities'  # Should be bad
            }
        ]
        
        with open(edges_file, 'w') as f:
            for edge in edges:
                json.dump(edge, f)
                f.write('\n')
        
        with open(nodes_file, 'w') as f:
            json.dump({'id': 'CHEBI:28748'}, f)
            f.write('\n')
            json.dump({'id': 'UniProtKB:P18887'}, f)
        
        classifier = EdgeClassifier(str(edges_file), str(nodes_file), str(output_dir))
        classifier.run_streaming(max_edges=2, batch_size=1000)
        
        # Check that we got some good edges (not all bad due to missing synonyms bug)
        good_edges_file = output_dir / "good_edges.jsonl"
        bad_edges_file = output_dir / "bad_edges.jsonl"
        
        assert good_edges_file.exists()
        assert bad_edges_file.exists()
        
        # Count edges
        good_count = sum(1 for _ in open(good_edges_file))
        bad_count = sum(1 for _ in open(bad_edges_file))
        
        # Should have at least 1 good edge (the first one with entities present)
        assert good_count >= 1
        # Should have at least 1 bad edge (the second one without entities)
        assert bad_count >= 1

    def test_streaming_ambiguous_classification_fix(self, tmp_path):
        """Test that streaming classification properly returns ambiguous edges."""
        # Create test files
        edges_file = tmp_path / "test_edges.jsonl"
        nodes_file = tmp_path / "test_nodes.jsonl"
        
        # Edge where ambiguity should be detected
        test_edge = {
            "subject": "CHEBI:12345",
            "object": "UniProtKB:P12345", 
            "sentences": "insulin and protein found in text"
        }
        
        with open(edges_file, 'w') as f:
            f.write(json.dumps(test_edge) + '\n')
            
        with open(nodes_file, 'w') as f:
            f.write("{}\n")
        
        # Setup classifier
        classifier = EdgeClassifier(str(edges_file), str(nodes_file), str(tmp_path / "output"))
        
        # Mock data that would cause ambiguity
        normalized_data = {
            'CHEBI:12345': {'id': {'identifier': 'CHEBI:12345'}},
            'UniProtKB:P12345': {'id': {'identifier': 'UniProtKB:P12345'}}
        }
        
        synonyms_data = {
            'CHEBI:12345': {'names': ['insulin']},
            'UniProtKB:P12345': {'names': ['protein']}
        }
        
        # Create lookup cache with multiple matches for 'insulin' (ambiguous case)
        lookup_cache = {
            'insulin': [
                {'curie': 'CHEBI:28748', 'label': 'insulin human', 'score': 1.0},
                {'curie': 'CHEBI:64816', 'label': 'different insulin', 'score': 1.0}
            ],
            'protein': [
                {'curie': 'UniProtKB:P12345', 'label': 'protein', 'score': 1.0}
            ]
        }
        
        # Test the classification
        classification, debug_info = classifier.classify_edge(
            test_edge, lookup_cache, normalized_data, synonyms_data
        )
        
        # Should return 'ambiguous' due to multiple insulin matches
        assert classification == 'ambiguous', f"Expected 'ambiguous', got '{classification}'"
        assert debug_info['subject_ambiguous'] == True

    def test_streaming_cache_ambiguity_logic_bug(self):
        """Test that verifies the fix for _check_entity_in_text_with_cache logic."""
        edges_file = "dummy_edges.jsonl"
        nodes_file = "dummy_nodes.jsonl"
        classifier = EdgeClassifier(edges_file, nodes_file, "dummy_output")
        
        # Test the _check_entity_in_text_with_cache method directly
        text = "insulin causes diabetes"
        synonyms = ['insulin']
        
        # Create lookup cache with multiple matches (should be ambiguous)
        lookup_cache = {
            'insulin': [
                {'curie': 'CHEBI:28748', 'label': 'human insulin', 'score': 1.0},
                {'curie': 'CHEBI:64816', 'label': 'different insulin', 'score': 1.0}
            ]
        }
        
        debug_info = {}
        
        # After fix: this should return True because entity is found in text (ambiguity handled separately)
        result = classifier._check_entity_in_text_with_cache(text, synonyms, lookup_cache, debug_info, 'subject')
        
        # After fix: ambiguous entities now return True (found) and ambiguity is handled separately
        assert result == True, "Ambiguous entities should return True after fix (entity found in text)"
        assert debug_info['subject_ambiguous'] == True, "Should be marked as ambiguous"
        
    def test_streaming_cache_non_ambiguous_logic(self):
        """Test _check_entity_in_text_with_cache with non-ambiguous case."""
        edges_file = "dummy_edges.jsonl" 
        nodes_file = "dummy_nodes.jsonl"
        classifier = EdgeClassifier(edges_file, nodes_file, "dummy_output")
        
        text = "insulin causes diabetes"
        synonyms = ['insulin']
        
        # Single match - not ambiguous
        lookup_cache = {
            'insulin': [
                {'curie': 'CHEBI:28748', 'label': 'insulin', 'score': 1.0}
            ]
        }
        
        debug_info = {}
        result = classifier._check_entity_in_text_with_cache(text, synonyms, lookup_cache, debug_info, 'subject')
        
        assert result == True, "Non-ambiguous entities should return True"
        assert debug_info['subject_ambiguous'] == False, "Should not be marked as ambiguous"

    def test_streaming_cache_preferred_name_disambiguation(self):
        """Test that preferred name logic works in cache version."""
        edges_file = "dummy_edges.jsonl"
        nodes_file = "dummy_nodes.jsonl"
        classifier = EdgeClassifier(edges_file, nodes_file, "dummy_output")
        
        text = "doxorubicin treats cancer"
        synonyms = ['doxorubicin']
        
        # Multiple matches but one has preferred name matching
        lookup_cache = {
            'doxorubicin': [
                {'curie': 'CHEBI:28748', 'label': 'doxorubicin', 'score': 1.0},  # Preferred name match
                {'curie': 'CHEBI:64816', 'label': 'adriamycin', 'score': 1.0}    # Different preferred name
            ]
        }
        
        debug_info = {}
        result = classifier._check_entity_in_text_with_cache(text, synonyms, lookup_cache, debug_info, 'subject')
        
        assert result == True, "Should resolve ambiguity using preferred name logic"
        assert debug_info['subject_ambiguous'] == False, "Should not be ambiguous after preferred name resolution"

    def test_check_ambiguous_matches_with_cache_filtering(self):
        """Test that check_ambiguous_matches_with_cache properly filters results."""
        edges_file = "dummy_edges.jsonl"
        nodes_file = "dummy_nodes.jsonl"
        classifier = EdgeClassifier(edges_file, nodes_file, "dummy_output")
        
        synonyms = ['doxorubicin']
        
        # Multiple matches but one has preferred name
        lookup_cache = {
            'doxorubicin': [
                {'curie': 'CHEBI:28748', 'label': 'doxorubicin', 'score': 1.0},  # Should be kept
                {'curie': 'CHEBI:64816', 'label': 'adriamycin', 'score': 1.0}    # Should be filtered out
            ]
        }
        
        is_ambiguous, filtered_lookup_data = classifier.check_ambiguous_matches_with_cache(synonyms, lookup_cache)
        
        assert not is_ambiguous, "Should not be ambiguous after preferred name filtering"
        assert len(filtered_lookup_data['doxorubicin']) == 1, "Should filter to only preferred match"
        assert filtered_lookup_data['doxorubicin'][0]['label'] == 'doxorubicin', "Should keep the preferred name match"


    def test_direct_classify_edge_ambiguous_bug(self):
        """Test the classify_edge method directly with ambiguous data."""
        edges_file = "dummy_edges.jsonl"
        nodes_file = "dummy_nodes.jsonl"
        classifier = EdgeClassifier(edges_file, nodes_file, "dummy_output")
        
        # Create test edge
        test_edge = {
            "subject": "CHEBI:12345",
            "object": "CHEBI:67890",
            "sentences": "insulin and glucose are both important"
        }
        
        # Mock data
        normalized_data = {
            'CHEBI:12345': {'id': {'identifier': 'CHEBI:12345'}},
            'CHEBI:67890': {'id': {'identifier': 'CHEBI:67890'}}
        }
        
        synonyms_data = {
            'CHEBI:12345': {'names': ['insulin']},
            'CHEBI:67890': {'names': ['glucose']}
        }
        
        # Create lookup cache with multiple matches for insulin (truly ambiguous - no preferred name match)
        lookup_cache = {
            'insulin': [
                {'curie': 'CHEBI:11111', 'label': 'human insulin', 'score': 1.0},
                {'curie': 'CHEBI:22222', 'label': 'porcine insulin', 'score': 1.0}
            ],
            'glucose': [
                {'curie': 'CHEBI:33333', 'label': 'D-glucose', 'score': 1.0}
            ]
        }
        
        # Test classification
        classification, debug_info = classifier.classify_edge(
            test_edge, lookup_cache, normalized_data, synonyms_data
        )
        
        print(f"Classification: {classification}")
        print(f"Debug info: {debug_info}")
        
        # After the fix, this should now correctly classify as 'ambiguous'
        assert classification == 'ambiguous', f"With the fix, ambiguous entities should be classified as 'ambiguous', got '{classification}'"
        assert debug_info.get('subject_ambiguous') == True, "Subject should be marked as ambiguous"
        assert debug_info.get('object_ambiguous') == False, "Object should not be ambiguous (single match)"

    def test_get_exact_matches_no_score_filtering(self):
        """Test that get_exact_matches returns all results without score filtering."""
        from api_functions import get_exact_matches
        
        # Test data with different scores
        lookup_results = [
            {'curie': 'CHEBI:1', 'label': 'compound1', 'score': 1.0},
            {'curie': 'CHEBI:2', 'label': 'compound2', 'score': 0.9},  # Lower score
            {'curie': 'CHEBI:3', 'label': 'compound3', 'score': 1.0}   # Same high score
        ]
        
        # Should return all results, not just highest scoring ones
        exact_matches = get_exact_matches(lookup_results)
        assert len(exact_matches) == 3, f"Expected 3 results, got {len(exact_matches)}"
        assert exact_matches == lookup_results, "Should return all results unchanged"
        
        # Test empty case
        assert get_exact_matches([]) == []
        assert get_exact_matches(None) == []

    def test_real_api_lookup_for_ambiguous_terms(self):
        """Test real API lookup for terms that should be ambiguous."""
        # Skip this test if we don't want to make real API calls during CI
        # Remove the skip to run with real API
        # pytest.skip("Skipping real API test - remove this line to test with real API")
        
        from api_functions import lookup_names, get_exact_matches
        
        # Test a term that should have multiple matches
        results = lookup_names("insulin", limit=10)
        print(f"Insulin lookup returned {len(results)} results")
        for result in results[:5]:  # Show first 5
            print(f"  {result.get('curie', 'N/A')}: {result.get('label', 'N/A')} (score: {result.get('score', 'N/A')})")
        
        # Test get_exact_matches on real data
        exact_matches = get_exact_matches(results)
        print(f"get_exact_matches returned {len(exact_matches)} results")
        
        # Should return all results now (no score filtering)
        assert len(exact_matches) == len(results), "get_exact_matches should return all results"

    def test_bulk_lookup_names_integration_fsh(self):
        """Integration test for bulk_lookup_names with FSH to verify GTOPDB entries are returned."""
        # Skip by default to avoid hitting API during regular tests
        # pytest.skip("Skipping integration test - remove this line to test with real API")
        
        from api_functions import bulk_lookup_names
        
        # Test FSH lookup which should return multiple GTOPDB entries
        try:
            results = bulk_lookup_names(['FSH'], limit=20)
            
            # Should have FSH in results
            assert 'FSH' in results, "FSH should be in bulk lookup results"
            
            # Get GTOPDB entries
            fsh_results = results['FSH']
            gtopdb_results = [r for r in fsh_results if r['curie'].startswith('GTOPDB:')]
            
            print(f"Found {len(gtopdb_results)} GTOPDB results for FSH:")
            for result in gtopdb_results:
                print(f"  {result['curie']} - {result['label']}")
            
            # Should have at least 2 GTOPDB entries (the ambiguous case)
            assert len(gtopdb_results) >= 2, f"Expected at least 2 GTOPDB results for FSH, got {len(gtopdb_results)}"
            
            # Verify we have the specific GTOPDB entries we expect
            gtopdb_curies = [r['curie'] for r in gtopdb_results]
            expected_curies = ['GTOPDB:4386', 'GTOPDB:4387']
            
            for expected_curie in expected_curies:
                assert expected_curie in gtopdb_curies, f"Expected {expected_curie} in GTOPDB results: {gtopdb_curies}"
            
            print("✓ Integration test passed: FSH returns expected GTOPDB ambiguous entries")
            
        except Exception as e:
            print(f"Integration test failed: {e}")
            raise


if __name__ == '__main__':
    pytest.main([__file__])