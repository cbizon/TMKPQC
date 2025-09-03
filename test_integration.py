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
    bulk_lookup_names,
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
        
        # Empty strings list should return empty dict
        result = bulk_lookup_names([])
        assert isinstance(result, dict)
        assert len(result) == 0
        
    def test_bulk_lookup_names_basic(self):
        """Test basic bulk lookup with real API."""
        strings = ["doxorubicin", "insulin", "water"]
        result = bulk_lookup_names(strings, limit=3)
        
        assert isinstance(result, dict)
        # Should have entries for all input strings
        for string in strings:
            assert string in result
            assert isinstance(result[string], list)
            # Each string should have at least one result (assuming they're common terms)
            if result[string]:  # If there are results
                first_result = result[string][0]
                assert "curie" in first_result
                assert "label" in first_result
                
    def test_bulk_lookup_vs_individual_comparison(self):
        """Compare results between bulk lookup and individual lookups."""
        test_strings = ["aspirin", "caffeine"]
        
        # Get results via bulk lookup
        bulk_results = bulk_lookup_names(test_strings, limit=5)
        
        # Get results via individual lookups
        individual_results = {}
        for string in test_strings:
            individual_results[string] = lookup_names(string, limit=5)
        
        # Compare results - they should be equivalent
        for string in test_strings:
            bulk_list = bulk_results.get(string, [])
            individual_list = individual_results.get(string, [])
            
            # Should have same number of results
            assert len(bulk_list) == len(individual_list)
            
            # If there are results, check that CURIEs match
            if bulk_list and individual_list:
                bulk_curies = {result.get("curie") for result in bulk_list}
                individual_curies = {result.get("curie") for result in individual_list}
                assert bulk_curies == individual_curies
                
    def test_bulk_lookup_with_filters(self):
        """Test bulk lookup with biolink type filter."""
        strings = ["insulin", "water"]
        result = bulk_lookup_names(strings, biolink_types=["SmallMolecule"], limit=3)
        
        assert isinstance(result, dict)
        for string in strings:
            if string in result and result[string]:
                # Check that results have the expected type (if available)
                first_result = result[string][0]
                assert "curie" in first_result


@pytest.mark.slow
class TestAPIIntegrationSlow:
    """Slower integration tests that test larger batches."""
    
    def test_bulk_lookup_performance_vs_individual(self):
        """Test performance difference between bulk and individual lookups."""
        import time
        
        test_strings = ["doxorubicin", "insulin", "aspirin", "caffeine", "water", 
                       "glucose", "sodium", "alcohol", "nicotine", "morphine"]
        
        # Time individual lookups
        start_time = time.time()
        individual_results = {}
        for string in test_strings:
            individual_results[string] = lookup_names(string, limit=5)
        individual_time = time.time() - start_time
        
        # Time bulk lookup
        start_time = time.time()
        bulk_results = bulk_lookup_names(test_strings, limit=5)
        bulk_time = time.time() - start_time
        
        print(f"\nPerformance comparison for {len(test_strings)} lookups:")
        print(f"Individual lookups: {individual_time:.3f} seconds")
        print(f"Bulk lookup: {bulk_time:.3f} seconds")
        print(f"Speed improvement: {individual_time/bulk_time:.2f}x faster")
        
        # Bulk should be significantly faster
        assert bulk_time < individual_time
        # Should be at least 2x faster (conservative estimate)
        assert individual_time / bulk_time >= 2.0
        
        # Verify results are equivalent
        for string in test_strings:
            bulk_list = bulk_results.get(string, [])
            individual_list = individual_results.get(string, [])
            assert len(bulk_list) == len(individual_list)
    
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