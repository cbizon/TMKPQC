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
    
    def test_load_data(self, temp_files):
        """Test loading data from files."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        classifier.load_data()
        
        assert len(classifier.edges) == 2
        assert len(classifier.nodes) == 2
        assert "CHEBI:28748" in classifier.nodes
        assert "UniProtKB:P18887" in classifier.nodes
        
        # Check that edge IDs were added
        for edge in classifier.edges:
            assert 'edge_id' in edge
    
    def test_load_data_with_limit(self, temp_files):
        """Test loading data with max_edges limit."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        classifier.load_data(max_edges=1)
        
        assert len(classifier.edges) == 1
        assert len(classifier.nodes) == 2  # Nodes should load completely
    
    def test_collect_entities(self, temp_files):
        """Test entity collection from edges."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        classifier.load_data()
        
        entities = classifier.collect_entities()
        
        expected_entities = {"CHEBI:28748", "UniProtKB:P18887", "UniProtKB:P99999"}
        assert entities == expected_entities
    
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
    
    @patch('phase1.lookup_names')
    def test_check_ambiguous_matches(self, mock_lookup, temp_files):
        """Test checking for ambiguous matches."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        # Mock lookup results with multiple exact synonym matches (ambiguous)
        mock_lookup.return_value = [
            {
                "curie": "CHEBI:28748", 
                "synonyms": ["doxorubicin", "adriamycin"]
            },
            {
                "curie": "CHEBI:99999", 
                "synonyms": ["doxorubicin", "other_name"]  # Also has doxorubicin = ambiguous
            }
        ]
        
        is_ambiguous, lookup_data = classifier.check_ambiguous_matches(["doxorubicin"])
        assert is_ambiguous is True
        assert "doxorubicin" in lookup_data
        assert len(lookup_data["doxorubicin"]) == 2  # Two matches = ambiguous
        
        # Mock lookup results with no exact synonym matches (unambiguous)
        mock_lookup.return_value = [
            {"curie": "CHEBI:28748", "synonyms": ["adriamycin", "other"]},  # No doxorubicin = unambiguous
            {"curie": "CHEBI:99999", "synonyms": ["different", "names"]}
        ]
        
        is_ambiguous, lookup_data = classifier.check_ambiguous_matches(["doxorubicin"])
        assert is_ambiguous is False
        assert lookup_data["doxorubicin"] == []  # No exact matches
    
    def test_classify_edge_no_text(self, temp_files):
        """Test classifying edge with no supporting text."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        edge = {
            "subject": "CHEBI:28748",
            "object": "UniProtKB:P18887",
            "sentences": ""
        }
        
        classification, debug_info = classifier.classify_edge(edge)
        assert classification == "bad"
    
    def test_classify_edge_na_text(self, temp_files):
        """Test classifying edge with NA text."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        edge = {
            "subject": "CHEBI:28748", 
            "object": "UniProtKB:P18887",
            "sentences": "NA"
        }
        
        classification, debug_info = classifier.classify_edge(edge)
        assert classification == "bad"
    
    @patch('phase1.EdgeClassifier.check_ambiguous_matches')
    def test_classify_edge_good(self, mock_ambiguous, temp_files):
        """Test classifying a good edge."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        # Mock normalized entities
        classifier.normalized_entities = {
            "CHEBI:28748": {
                "id": {"identifier": "CHEBI:28748"},
                "type": ["biolink:SmallMolecule"]
            },
            "UniProtKB:P18887": {
                "id": {"identifier": "UniProtKB:P18887"},
                "type": ["biolink:Protein"]
            }
        }
        
        # Mock synonyms data
        classifier.synonyms_data = {
            "CHEBI:28748": {"names": ["doxorubicin", "adriamycin"]},
            "UniProtKB:P18887": {"names": ["XRCC1", "XRCC1_HUMAN"]}
        }
        
        # Mock no ambiguous matches
        mock_ambiguous.return_value = (False, {})
        
        edge = {
            "subject": "CHEBI:28748",
            "object": "UniProtKB:P18887", 
            "sentences": "Doxorubicin increases XRCC1 expression in cells."
        }
        
        classification, debug_info = classifier.classify_edge(edge)
        assert classification == "good"
    
    @patch('phase1.EdgeClassifier.check_ambiguous_matches')
    def test_classify_edge_ambiguous(self, mock_ambiguous, temp_files):
        """Test classifying an ambiguous edge."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        # Mock normalized entities
        classifier.normalized_entities = {
            "CHEBI:28748": {
                "id": {"identifier": "CHEBI:28748"},
                "type": ["biolink:SmallMolecule"]
            },
            "UniProtKB:P18887": {
                "id": {"identifier": "UniProtKB:P18887"}, 
                "type": ["biolink:Protein"]
            }
        }
        
        # Mock synonyms data
        classifier.synonyms_data = {
            "CHEBI:28748": {"names": ["doxorubicin"]},
            "UniProtKB:P18887": {"names": ["XRCC1"]}
        }
        
        # Mock ambiguous matches found
        mock_ambiguous.return_value = (True, {})
        
        edge = {
            "subject": "CHEBI:28748",
            "object": "UniProtKB:P18887",
            "sentences": "Doxorubicin increases XRCC1 expression in cells."
        }
        
        classification, debug_info = classifier.classify_edge(edge)
        assert classification == "ambiguous"
    
    def test_classify_edge_missing_entity(self, temp_files):
        """Test classifying edge where only one entity is mentioned."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        
        # Mock normalized entities
        classifier.normalized_entities = {
            "CHEBI:28748": {
                "id": {"identifier": "CHEBI:28748"},
                "type": ["biolink:SmallMolecule"] 
            },
            "UniProtKB:P18887": {
                "id": {"identifier": "UniProtKB:P18887"},
                "type": ["biolink:Protein"]
            }
        }
        
        # Mock synonyms data
        classifier.synonyms_data = {
            "CHEBI:28748": {"names": ["doxorubicin"]},
            "UniProtKB:P18887": {"names": ["XRCC1"]}
        }
        
        edge = {
            "subject": "CHEBI:28748",
            "object": "UniProtKB:P18887",
            "sentences": "Doxorubicin was administered to patients."  # No mention of XRCC1
        }
        
        classification, debug_info = classifier.classify_edge(edge)
        assert classification == "bad"
    
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
    
    @patch('phase1.EdgeClassifier.classify_edge')
    @patch('phase1.EdgeClassifier.write_edge_result')
    def test_process_all_edges(self, mock_write, mock_classify, temp_files):
        """Test processing all edges."""
        edges_file, nodes_file, output_dir = temp_files
        
        classifier = EdgeClassifier(edges_file, nodes_file, output_dir)
        classifier.load_data()
        
        # Mock classifications
        mock_classify.side_effect = [("good", {}), ("bad", {})]
        
        results = classifier.process_all_edges()
        
        assert results == {"good": 1, "bad": 1}
        assert mock_classify.call_count == 2
        assert mock_write.call_count == 2


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
        
        # Temporarily use legacy processing to avoid bulk lookup issues
        with patch.object(classifier, 'process_all_edges_batched', classifier.process_all_edges):
            classifier.run(max_edges=1)
        
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
    
    def test_check_ambiguous_matches_with_exact_synonyms(self):
        """Test check_ambiguous_matches with exact synonym matching logic."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        # Test case 1: Single exact match (not ambiguous)
        with patch('phase1.lookup_names') as mock_lookup:
            mock_lookup.return_value = [
                {
                    'curie': 'NCBIGene:5133',
                    'label': 'PDCD1',
                    'synonyms': ['PD-1', 'PDCD1', 'programmed cell death 1']
                },
                {
                    'curie': 'NCBIGene:100526842', 
                    'label': 'RPL17-C18orf32',
                    'synonyms': ['RPL17', 'C18orf32']  # PD-1 NOT in synonyms
                }
            ]
            
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['PD-1'])
            assert is_ambiguous == False  # Not ambiguous - only one exact match
            assert 'PD-1' in lookup_data
            assert len(lookup_data['PD-1']) == 1
            
        # Test case 2: Multiple exact matches (ambiguous)
        with patch('phase1.lookup_names') as mock_lookup:
            mock_lookup.return_value = [
                {
                    'curie': 'NCBIGene:5133',
                    'label': 'PDCD1',
                    'synonyms': ['PD-1', 'PDCD1', 'programmed cell death 1']
                },
                {
                    'curie': 'NCBIGene:100526842',
                    'label': 'RPL17-C18orf32', 
                    'synonyms': ['PD-1', 'RPL17', 'C18orf32']  # PD-1 IS in synonyms
                }
            ]
            
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['PD-1'])
            assert is_ambiguous == True  # Ambiguous - two exact matches
            assert 'PD-1' in lookup_data
            assert len(lookup_data['PD-1']) == 2
            
        # Test case 3: Gene with taxon filter
        with patch('phase1.lookup_names') as mock_lookup:
            mock_lookup.return_value = [
                {
                    'curie': 'NCBIGene:5133',
                    'label': 'PDCD1',
                    'synonyms': ['PD-1', 'PDCD1']
                }
            ]
            
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['PD-1'], expected_biolink_type='Gene')
            assert is_ambiguous == False
            assert 'PD-1' in lookup_data
            
            # Verify taxon filter was applied
            mock_lookup.assert_called_with(
                query='PD-1',
                limit=20,
                biolink_type='Gene',
                only_taxa=['NCBITaxon:9606']
            )
    
    def test_strict_exact_synonym_matching(self):
        """Test that synonym matching requires exact string match, not substring."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        # Test case: Substring should NOT match (strict exact matching)
        with patch('phase1.lookup_names') as mock_lookup:
            mock_lookup.return_value = [
                {
                    'curie': 'CHEBI:28748',
                    'label': 'Doxorubicin',
                    'synonyms': ['doxorubicin', 'DOX', 'Adriamycin']  # Has exact match
                },
                {
                    'curie': 'UNII:27844X2J29',
                    'label': 'Zoptarelin doxorubicin',
                    'synonyms': ['ZOPTARELIN DOXORUBICIN', 'Zoptarelin doxorubicin']  # Contains but not exact
                }
            ]
            
            # Should NOT be ambiguous because only one has exact 'doxorubicin' synonym
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['doxorubicin'])
            assert is_ambiguous == False  # Not ambiguous - only one exact match
            assert 'doxorubicin' in lookup_data
            assert len(lookup_data['doxorubicin']) == 1
            assert lookup_data['doxorubicin'][0]['curie'] == 'CHEBI:28748'
        
        # Test case: Multiple exact matches should be ambiguous  
        with patch('phase1.lookup_names') as mock_lookup:
            mock_lookup.return_value = [
                {
                    'curie': 'CHEBI:28748',
                    'label': 'Adriamycin',  # Different preferred name, not "doxorubicin"
                    'synonyms': ['doxorubicin', 'DOX', 'Adriamycin']
                },
                {
                    'curie': 'CHEBI:64816', 
                    'label': 'doxorubicin(1+)',
                    'synonyms': ['doxorubicin', 'doxorubicin cation']  # Also has exact match
                }
            ]
            
            # Should be ambiguous because both have exact 'doxorubicin' synonym 
            # and neither has 'doxorubicin' as preferred name
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['doxorubicin'])
            assert is_ambiguous == True  # Ambiguous - two exact matches, no preferred name match
            assert len(lookup_data['doxorubicin']) == 2
    
    def test_lookup_data_storage_comprehensive(self):
        """Test comprehensive lookup data storage functionality."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        with patch('phase1.lookup_names') as mock_lookup:
            # Mock different results for different synonyms
            def mock_lookup_side_effect(query, **kwargs):
                if query == "doxorubicin":
                    return [
                        {'curie': 'CHEBI:28748', 'label': 'Doxorubicin', 'taxa': [], 'score': 9395.26, 'synonyms': ['doxorubicin', 'DOX'], 'types': ['biolink:SmallMolecule']},
                        {'curie': 'CHEBI:64816', 'label': 'doxorubicin(1+)', 'taxa': [], 'score': 447.19, 'synonyms': ['doxorubicin'], 'types': ['biolink:SmallMolecule']}
                    ]
                elif query == "Doxorubicin":
                    return [
                        {'curie': 'CHEBI:28748', 'label': 'Doxorubicin', 'taxa': [], 'score': 9395.26, 'synonyms': ['Doxorubicin', 'DOX'], 'types': ['biolink:SmallMolecule']}
                    ]
                elif query == "XRCC1":
                    return [
                        {'curie': 'NCBIGene:7515', 'label': 'XRCC1', 'taxa': ['NCBITaxon:9606'], 'score': 3314.64, 'synonyms': ['XRCC1'], 'types': ['biolink:Gene']}
                    ]
                return []
            
            mock_lookup.side_effect = mock_lookup_side_effect
            
            # Test multiple synonyms with different ambiguity levels
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['doxorubicin', 'Doxorubicin', 'XRCC1'])
            
            # Should NOT be ambiguous because 'doxorubicin' has one match with 'Doxorubicin' as preferred name
            assert is_ambiguous == False
            
            # Check lookup data structure
            assert 'doxorubicin' in lookup_data
            assert 'Doxorubicin' in lookup_data  
            assert 'XRCC1' in lookup_data
            
            # Check exact match counts (enhanced logic applied)
            assert len(lookup_data['doxorubicin']) == 1  # Resolved by preferred name logic
            assert lookup_data['doxorubicin'][0]['curie'] == 'CHEBI:28748'  # The one with preferred name
            assert len(lookup_data['Doxorubicin']) == 1  # Not ambiguous
            assert len(lookup_data['XRCC1']) == 1  # Not ambiguous
            
            # Check data structure completeness
            for synonym, matches in lookup_data.items():
                for match in matches:
                    assert 'curie' in match
                    assert 'label' in match
                    assert 'taxa' in match
                    assert 'score' in match
                    assert 'synonyms' in match
                    assert 'types' in match
    
    def test_gene_taxon_filtering(self):
        """Test that genes are filtered by human taxon."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        with patch('phase1.lookup_names') as mock_lookup:
            mock_lookup.return_value = [
                {'curie': 'NCBIGene:7515', 'label': 'XRCC1', 'taxa': ['NCBITaxon:9606'], 'score': 100, 'synonyms': ['XRCC1'], 'types': ['biolink:Gene']}
            ]
            
            # Call with gene biolink type
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['XRCC1'], 'Gene')
            
            # Verify lookup_names was called with human taxon filter
            mock_lookup.assert_called_with(
                query='XRCC1',
                limit=20,
                biolink_type='Gene',
                only_taxa=['NCBITaxon:9606']
            )
            
            assert not is_ambiguous
            assert len(lookup_data['XRCC1']) == 1
    
    def test_enhanced_preferred_name_logic_doxorubicin_case(self):
        """Test enhanced logic: doxorubicin case where one match has preferred name."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        with patch('phase1.lookup_names') as mock_lookup:
            # Simulate doxorubicin case: one match has "Doxorubicin" as preferred name
            mock_lookup.return_value = [
                {
                    'curie': 'CHEBI:28748',
                    'label': 'Doxorubicin',  # Preferred name matches synonym
                    'synonyms': ['doxorubicin', 'Doxorubicin', 'ADR', 'DOX'],
                    'score': 9395.26,
                    'types': ['biolink:SmallMolecule']
                },
                {
                    'curie': 'CHEBI:64816', 
                    'label': 'doxorubicin(1+)',  # Different preferred name
                    'synonyms': ['doxorubicin', 'doxorubicin cation'],
                    'score': 447.19,
                    'types': ['biolink:SmallMolecule']
                }
            ]
            
            # Should NOT be ambiguous - one match has "Doxorubicin" as preferred name
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['Doxorubicin'])
            assert not is_ambiguous
            assert len(lookup_data['Doxorubicin']) == 1
            assert lookup_data['Doxorubicin'][0]['curie'] == 'CHEBI:28748'
            assert lookup_data['Doxorubicin'][0]['label'] == 'Doxorubicin'
    
    def test_enhanced_preferred_name_logic_fsh_case(self):
        """Test enhanced logic: FSH case where multiple matches have preferred name."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        with patch('phase1.lookup_names') as mock_lookup:
            # Simulate FSH case: multiple matches have "FSH" as preferred name
            mock_lookup.return_value = [
                {
                    'curie': 'GTOPDB:4386',
                    'label': 'FSH',  # Preferred name matches synonym
                    'synonyms': ['FSH', '4384', '4377'],
                    'score': 1296.71,
                    'types': ['biolink:SmallMolecule']
                },
                {
                    'curie': 'GTOPDB:4387',
                    'label': 'FSH',  # Also has FSH as preferred name
                    'synonyms': ['FSH', '4385', '4378'],
                    'score': 1296.71,
                    'types': ['biolink:SmallMolecule']
                },
                {
                    'curie': 'CHEBI:81569',
                    'label': 'Follitropin',  # Different preferred name
                    'synonyms': ['FSH', '3733', 'fshs', '3731'],
                    'score': 38.15,
                    'types': ['biolink:SmallMolecule']
                }
            ]
            
            # Should REMAIN ambiguous - multiple matches have "FSH" as preferred name
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['FSH'])
            assert is_ambiguous
            assert len(lookup_data['FSH']) == 3  # All matches kept
    
    def test_enhanced_preferred_name_logic_no_preferred_match(self):
        """Test enhanced logic: no match has synonym as preferred name."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        with patch('phase1.lookup_names') as mock_lookup:
            # Case where synonym appears in multiple results but none as preferred name
            mock_lookup.return_value = [
                {
                    'curie': 'CHEBI:12345',
                    'label': 'Chemical A',  # Different preferred name
                    'synonyms': ['test_synonym', 'alt1'],
                    'score': 100,
                    'types': ['biolink:SmallMolecule']
                },
                {
                    'curie': 'CHEBI:67890',
                    'label': 'Chemical B',  # Different preferred name  
                    'synonyms': ['test_synonym', 'alt2'],
                    'score': 90,
                    'types': ['biolink:SmallMolecule']
                }
            ]
            
            # Should REMAIN ambiguous - no match has synonym as preferred name
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['test_synonym'])
            assert is_ambiguous
            assert len(lookup_data['test_synonym']) == 2  # All matches kept
    
    def test_enhanced_preferred_name_logic_case_insensitive(self):
        """Test enhanced logic: case-insensitive matching of preferred names."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        with patch('phase1.lookup_names') as mock_lookup:
            # Test case-insensitive matching
            mock_lookup.return_value = [
                {
                    'curie': 'CHEBI:11111',
                    'label': 'INSULIN',  # Uppercase preferred name
                    'synonyms': ['insulin', 'INSULIN', 'Insulin'],
                    'score': 100,
                    'types': ['biolink:SmallMolecule']
                },
                {
                    'curie': 'CHEBI:22222',
                    'label': 'insulin receptor',  # Different preferred name
                    'synonyms': ['insulin', 'INSR'],
                    'score': 50,
                    'types': ['biolink:Protein']
                }
            ]
            
            # Should NOT be ambiguous - case-insensitive match of preferred name
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['insulin'])
            assert not is_ambiguous
            assert len(lookup_data['insulin']) == 1
            assert lookup_data['insulin'][0]['curie'] == 'CHEBI:11111'
            assert lookup_data['insulin'][0]['label'] == 'INSULIN'
    
    def test_enhanced_preferred_name_logic_single_match_unchanged(self):
        """Test enhanced logic: single match behavior unchanged."""
        classifier = EdgeClassifier("dummy_edges.jsonl", "dummy_nodes.jsonl")
        
        with patch('phase1.lookup_names') as mock_lookup:
            # Single match case - should work as before
            mock_lookup.return_value = [
                {
                    'curie': 'CHEBI:12345',
                    'label': 'Unique Chemical',
                    'synonyms': ['unique_synonym'],
                    'score': 100,
                    'types': ['biolink:SmallMolecule']
                }
            ]
            
            # Should NOT be ambiguous - single match
            is_ambiguous, lookup_data = classifier.check_ambiguous_matches(['unique_synonym'])
            assert not is_ambiguous
            assert len(lookup_data['unique_synonym']) == 1


if __name__ == '__main__':
    pytest.main([__file__])