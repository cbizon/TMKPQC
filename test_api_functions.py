"""
Tests for api_functions.py

These tests cover the API interaction functions for node normalization,
synonym retrieval, and name lookup.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests

from api_functions import (
    get_normalized_nodes,
    get_synonyms,
    lookup_names,
    batch_get_normalized_nodes,
    batch_get_synonyms,
    get_exact_matches,
    APIException
)


class TestGetNormalizedNodes:
    """Tests for get_normalized_nodes function."""
    
    def test_successful_request(self):
        """Test successful API request."""
        mock_response = {
            "MESH:D014867": {
                "id": {"identifier": "CHEBI:15377", "label": "Water"},
                "equivalent_identifiers": [
                    {"identifier": "CHEBI:15377", "label": "water"}
                ],
                "type": ["biolink:SmallMolecule"]
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None
            
            result = get_normalized_nodes(["MESH:D014867"])
            
            assert result == mock_response
            mock_post.assert_called_once()
            
            # Check that the request was made with correct parameters
            call_args = mock_post.call_args
            assert call_args[1]['json']['curies'] == ["MESH:D014867"]
            assert call_args[1]['json']['conflate'] is True
    
    def test_request_exception(self):
        """Test request exception handling."""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(APIException, match="Node normalizer API request failed"):
                get_normalized_nodes(["MESH:D014867"])
    
    def test_json_decode_error(self):
        """Test JSON decode error handling."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_post.return_value = mock_response
            
            with pytest.raises(APIException, match="Failed to parse node normalizer API response"):
                get_normalized_nodes(["MESH:D014867"])
    
    def test_custom_parameters(self):
        """Test request with custom parameters."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {}
            mock_post.return_value.raise_for_status.return_value = None
            
            get_normalized_nodes(
                ["MESH:D014867"],
                conflate=False,
                description=True,
                drug_chemical_conflate=False,
                individual_types=True
            )
            
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['conflate'] is False
            assert payload['description'] is True
            assert payload['drug_chemical_conflate'] is False
            assert payload['individual_types'] is True


class TestGetSynonyms:
    """Tests for get_synonyms function."""
    
    def test_successful_request(self):
        """Test successful synonyms request."""
        mock_response = {
            "MONDO:0005737": {
                "curie": "MONDO:0005737",
                "names": ["EHF", "Ebola", "Ebola fever"],
                "preferred_name": "Ebola hemorrhagic fever"
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None
            
            result = get_synonyms(["MONDO:0005737"])
            
            assert result == mock_response
            mock_post.assert_called_once()
    
    def test_request_exception(self):
        """Test request exception handling."""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(APIException, match="Name resolver synonyms API request failed"):
                get_synonyms(["MONDO:0005737"])


class TestLookupNames:
    """Tests for lookup_names function."""
    
    def test_successful_lookup(self):
        """Test successful name lookup."""
        mock_response = [
            {
                "curie": "CHEBI:28748",
                "label": "Doxorubicin",
                "synonyms": ["ADM", "ADR"],
                "score": 9395.258
            }
        ]
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status.return_value = None
            
            result = lookup_names("doxorubicin")
            
            assert result == mock_response
            mock_get.assert_called_once()
    
    def test_lookup_with_filters(self):
        """Test lookup with filtering parameters."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = []
            mock_get.return_value.raise_for_status.return_value = None
            
            lookup_names(
                "doxorubicin",
                biolink_type="SmallMolecule",
                only_prefixes=["CHEBI"],
                only_taxa=["NCBITaxon:9606"],
                limit=5
            )
            
            # Check that URL parameters were constructed correctly
            call_args = mock_get.call_args
            url = call_args[0][0]
            assert "biolink_type=SmallMolecule" in url
            assert "limit=5" in url
    
    def test_request_exception(self):
        """Test request exception handling."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(APIException, match="Name resolver lookup API request failed"):
                lookup_names("doxorubicin")


class TestBatchFunctions:
    """Tests for batch processing functions."""
    
    def test_batch_get_normalized_nodes(self):
        """Test batch processing of node normalization."""
        mock_response1 = {"CURIE1": {"id": {"identifier": "NORM1"}}}
        mock_response2 = {"CURIE2": {"id": {"identifier": "NORM2"}}}
        
        with patch('api_functions.get_normalized_nodes') as mock_get_norm:
            mock_get_norm.side_effect = [mock_response1, mock_response2]
            
            # Test with batch size smaller than input
            result = batch_get_normalized_nodes(
                ["CURIE1", "CURIE2", "CURIE3"], 
                batch_size=2
            )
            
            assert len(result) == 2
            assert result["CURIE1"] == mock_response1["CURIE1"]
            assert result["CURIE2"] == mock_response2["CURIE2"]
            assert mock_get_norm.call_count == 2
    
    def test_batch_get_synonyms(self):
        """Test batch processing of synonym retrieval."""
        mock_response1 = {"PREF1": {"names": ["name1"]}}
        mock_response2 = {"PREF2": {"names": ["name2"]}}
        
        with patch('api_functions.get_synonyms') as mock_get_syn:
            mock_get_syn.side_effect = [mock_response1, mock_response2]
            
            result = batch_get_synonyms(["PREF1", "PREF2"], batch_size=1)
            
            assert len(result) == 2
            assert result["PREF1"] == mock_response1["PREF1"]
            assert result["PREF2"] == mock_response2["PREF2"]
            assert mock_get_syn.call_count == 2


class TestGetExactMatches:
    """Tests for get_exact_matches function."""
    
    def test_single_exact_match(self):
        """Test with single exact match."""
        lookup_results = [
            {"curie": "CHEBI:28748", "score": 9395.258},
            {"curie": "CHEBI:64816", "score": 447.185}
        ]
        
        exact_matches = get_exact_matches(lookup_results)
        
        assert len(exact_matches) == 1
        assert exact_matches[0]["curie"] == "CHEBI:28748"
        assert exact_matches[0]["score"] == 9395.258
    
    def test_multiple_exact_matches(self):
        """Test with multiple exact matches (same highest score)."""
        lookup_results = [
            {"curie": "CHEBI:28748", "score": 9395.258},
            {"curie": "CHEBI:64816", "score": 9395.258},
            {"curie": "CHEBI:12345", "score": 447.185}
        ]
        
        exact_matches = get_exact_matches(lookup_results)
        
        assert len(exact_matches) == 2
        assert all(match["score"] == 9395.258 for match in exact_matches)
    
    def test_empty_results(self):
        """Test with empty lookup results."""
        exact_matches = get_exact_matches([])
        assert exact_matches == []
    
    def test_missing_scores(self):
        """Test with results missing score field."""
        lookup_results = [
            {"curie": "CHEBI:28748"},
            {"curie": "CHEBI:64816", "score": 447.185}
        ]
        
        exact_matches = get_exact_matches(lookup_results)
        
        assert len(exact_matches) == 1
        assert exact_matches[0]["curie"] == "CHEBI:64816"


class TestErrorHandling:
    """Tests for error handling across all functions."""
    
    def test_timeout_handling(self):
        """Test timeout exception handling."""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
            
            with pytest.raises(APIException):
                get_normalized_nodes(["MESH:D014867"])
    
    def test_http_error_handling(self):
        """Test HTTP error handling."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
            mock_post.return_value = mock_response
            
            with pytest.raises(APIException):
                get_normalized_nodes(["MESH:D014867"])


if __name__ == '__main__':
    pytest.main([__file__])