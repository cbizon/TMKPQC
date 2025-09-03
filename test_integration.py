"""
Integration tests for API functions.
These tests make actual API calls to verify functionality.
Run with: pytest test_integration.py -v
"""

import pytest
from api_functions import (
    get_normalized_nodes, 
    get_synonyms, 
    lookup_names,
    batch_get_normalized_nodes,
    batch_get_synonyms,
    APIException
)


class TestAPIIntegration:
    """Integration tests that make real API calls."""
    
    def test_get_normalized_nodes_basic(self):
        """Test basic node normalization with real API."""
        curies = ["CHEBI:28748", "HGNC:1100"]
        result = get_normalized_nodes(curies)
        
        assert isinstance(result, dict)
        # Should have entries for the input CURIEs
        assert "CHEBI:28748" in result or any("CHEBI:28748" in str(v) for v in result.values())
        
    def test_get_synonyms_basic(self):
        """Test basic synonym retrieval with real API."""
        # Use a known CURIE that should have synonyms
        preferred_curies = ["CHEBI:28748"]  # Doxorubicin
        result = get_synonyms(preferred_curies)
        
        assert isinstance(result, dict)
        # Should have an entry for our input CURIE
        assert "CHEBI:28748" in result or any("CHEBI:28748" in str(v) for v in result.values())
        
    def test_lookup_names_basic(self):
        """Test basic name lookup with real API."""
        result = lookup_names("doxorubicin", limit=5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Should have basic fields
        first_result = result[0]
        assert "curie" in first_result
        assert "label" in first_result
        
    def test_lookup_names_with_filters(self):
        """Test name lookup with biolink type filter."""
        result = lookup_names("insulin", biolink_type="SmallMolecule", limit=3)
        
        assert isinstance(result, list)
        if result:  # May return empty if no matches
            first_result = result[0]
            assert "curie" in first_result
            
    def test_batch_get_normalized_nodes_small(self):
        """Test batch normalization with small batch size."""
        curies = ["CHEBI:28748", "HGNC:1100", "MONDO:0007739"]
        result = batch_get_normalized_nodes(curies, batch_size=2)
        
        assert isinstance(result, dict)
        # Should process all CURIEs even with small batch size
        assert len(result) > 0
        
    def test_batch_get_synonyms_small(self):
        """Test batch synonyms with small batch size."""
        preferred_curies = ["CHEBI:28748", "HGNC:1100"]
        result = batch_get_synonyms(preferred_curies, batch_size=1)
        
        assert isinstance(result, dict)
        # Should process all CURIEs even with batch size of 1
        assert len(result) > 0
        
    def test_api_error_handling(self):
        """Test that invalid requests are handled gracefully."""
        # Invalid CURIEs return None for that CURIE, not an error
        result = get_normalized_nodes(["invalid_curie_format_123456789"])
        assert isinstance(result, dict)
        assert result["invalid_curie_format_123456789"] is None
            
    def test_empty_inputs(self):
        """Test API functions with empty inputs."""
        # Empty CURIE list causes 422 error for node normalizer
        with pytest.raises(APIException):
            get_normalized_nodes([])
        
        # Empty CURIE list returns empty dict for synonyms
        result = get_synonyms([])
        assert isinstance(result, dict)
        assert len(result) == 0
        
        # Empty query string should return empty list
        result = lookup_names("", limit=1)
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.slow
class TestAPIIntegrationSlow:
    """Slower integration tests that test larger batches."""
    
    def test_medium_batch_synonyms(self):
        """Test synonyms API with medium batch size to check for server errors."""
        # Test with batch size that previously caused 500 errors
        test_curies = [f"CHEBI:{i}" for i in range(28748, 28798)]  # 50 CURIEs
        
        try:
            result = batch_get_synonyms(test_curies, batch_size=25)
            assert isinstance(result, dict)
        except APIException as e:
            # If we get a server error, that's expected and helps identify the limit
            if "500" in str(e):
                pytest.skip(f"Server error with batch size 25: {e}")
            else:
                raise
                
    def test_lookup_performance(self):
        """Test lookup API performance with multiple calls."""
        test_terms = ["doxorubicin", "insulin", "aspirin", "caffeine", "water"]
        
        results = []
        for term in test_terms:
            result = lookup_names(term, limit=1)
            results.append(result)
            
        assert len(results) == 5
        # Each result should be a list
        for result in results:
            assert isinstance(result, list)


if __name__ == "__main__":
    # Run basic integration tests
    pytest.main([__file__, "-v", "-m", "not slow"])