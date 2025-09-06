"""
API functions for interacting with the node normalizer and name resolver services.
All functions use POST requests and batch processing for efficiency.
"""

import requests
import json
from typing import List, Dict, Any, Optional
import time
import random
from urllib.parse import urlencode


class APIException(Exception):
    """Custom exception for API-related errors."""
    pass


def api_request_with_retry(func, *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs):
    """
    Execute an API request with exponential backoff retry logic.
    
    Args:
        func: The API function to call
        *args: Arguments for the function
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the successful API call
        
    Raises:
        APIException: If all retry attempts fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except APIException as e:
            last_exception = e
            
            # Don't retry on the last attempt
            if attempt == max_retries:
                break
                
            # Check if this is a server error worth retrying (5xx errors)
            if "502 Server Error" in str(e) or "503 Server Error" in str(e) or "500 Server Error" in str(e):
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff + jitter
                print(f"API request failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                print(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                # Don't retry on non-server errors (4xx, network issues, etc.)
                raise e
    
    # All retries exhausted
    raise last_exception


def get_normalized_nodes(curies: List[str], 
                        conflate: bool = True, 
                        description: bool = False, 
                        drug_chemical_conflate: bool = True,
                        individual_types: bool = False) -> Dict[str, Any]:
    """
    Get normalized node information for a list of CURIEs using the node normalizer API.
    
    Args:
        curies: List of CURIEs to normalize
        conflate: Whether to apply gene/protein conflation (default: True)
        description: Whether to return CURIE descriptions when possible (default: False)
        drug_chemical_conflate: Whether to apply drug/chemical conflation (default: True)
        individual_types: Whether to return individual types for equivalent identifiers (default: False)
    
    Returns:
        Dictionary mapping input CURIEs to their normalized information
        
    Raises:
        APIException: If the API request fails
    """
    url = "https://nodenormalization-dev.apps.renci.org/get_normalized_nodes"
    
    payload = {
        "curies": curies,
        "conflate": conflate,
        "description": description,
        "drug_chemical_conflate": drug_chemical_conflate,
        "individual_types": individual_types
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIException(f"Node normalizer API request failed: {e}")
    except json.JSONDecodeError as e:
        raise APIException(f"Failed to parse node normalizer API response: {e}")


def get_synonyms(preferred_curies: List[str]) -> Dict[str, Any]:
    """
    Get synonyms for preferred CURIEs using the name resolver API.
    
    Args:
        preferred_curies: List of preferred CURIEs (must be normalized IDs)
    
    Returns:
        Dictionary mapping preferred CURIEs to their synonym information
        
    Raises:
        APIException: If the API request fails
    """
    url = "https://name-resolution-sri-dev.apps.renci.org/synonyms"
    
    payload = {
        "preferred_curies": preferred_curies
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIException(f"Name resolver synonyms API request failed: {e}")
    except json.JSONDecodeError as e:
        raise APIException(f"Failed to parse synonyms API response: {e}")


def lookup_names(query: str, 
                autocomplete: bool = False,
                highlighting: bool = False,
                offset: int = 0,
                limit: int = 10,
                biolink_type: Optional[str] = None,
                only_prefixes: Optional[List[str]] = None,
                exclude_prefixes: Optional[List[str]] = None,
                only_taxa: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Look up entities by name using the name resolver API.
    
    Args:
        query: Search term
        autocomplete: Enable autocomplete/partial matching (default: False)
        highlighting: Enable search term highlighting (default: False)
        offset: Number of results to skip for pagination (default: 0)
        limit: Maximum number of results (default: 10)
        biolink_type: Filter by Biolink entity type (e.g., 'SmallMolecule', 'Gene', 'Disease')
        only_prefixes: Only include results from these namespaces
        exclude_prefixes: Exclude results from these namespaces
        only_taxa: Only include results from these taxa (e.g., ['NCBITaxon:9606'] for humans)
    
    Returns:
        List of matching entities with their information
        
    Raises:
        APIException: If the API request fails
    """
    url = "https://name-resolution-sri-dev.apps.renci.org/lookup"
    
    params = {
        "string": query,
        "autocomplete": autocomplete,
        "highlighting": highlighting,
        "offset": offset,
        "limit": limit
    }
    
    if biolink_type:
        params["biolink_type"] = biolink_type
    if only_prefixes:
        params["only_prefixes"] = only_prefixes
    if exclude_prefixes:
        params["exclude_prefixes"] = exclude_prefixes
    if only_taxa:
        params["only_taxa"] = only_taxa
    
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{url}?{urlencode(params, doseq=True)}", 
                               headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIException(f"Name resolver lookup API request failed: {e}")
    except json.JSONDecodeError as e:
        raise APIException(f"Failed to parse lookup API response: {e}")


def batch_get_normalized_nodes(all_curies: List[str], batch_size: int = 2000) -> Dict[str, Any]:
    """
    Process a large list of CURIEs in batches for node normalization.
    
    Args:
        all_curies: Complete list of CURIEs to normalize
        batch_size: Size of each batch (default: 2000)
    
    Returns:
        Combined dictionary of all normalized node information
        
    Raises:
        APIException: If any API request fails
    """
    results = {}
    
    for i in range(0, len(all_curies), batch_size):
        batch = all_curies[i:i + batch_size]
        print(f"Processing node normalization batch {i//batch_size + 1} of {(len(all_curies) + batch_size - 1)//batch_size} ({len(batch)} curies)")
        
        batch_results = api_request_with_retry(get_normalized_nodes, batch)
        results.update(batch_results)
        
        # Small delay between batches to be respectful to the API
        if i + batch_size < len(all_curies):
            time.sleep(0.1)
    
    return results


def batch_get_synonyms(preferred_curies: List[str], batch_size: int = 500) -> Dict[str, Any]:
    """
    Process a large list of preferred CURIEs in batches for synonym retrieval.
    
    Args:
        preferred_curies: Complete list of preferred CURIEs
        batch_size: Size of each batch (default: 10000)
    
    Returns:
        Combined dictionary of all synonym information
        
    Raises:
        APIException: If any API request fails
    """
    results = {}
    
    for i in range(0, len(preferred_curies), batch_size):
        batch = preferred_curies[i:i + batch_size]
        print(f"Processing synonyms batch {i//batch_size + 1} of {(len(preferred_curies) + batch_size - 1)//batch_size} ({len(batch)} curies)")
        
        batch_results = api_request_with_retry(get_synonyms, batch)
        results.update(batch_results)
        
        # Small delay between batches to be respectful to the API
        if i + batch_size < len(preferred_curies):
            time.sleep(0.1)
    
    return results


def bulk_lookup_names(strings: List[str], 
                     autocomplete: bool = False,
                     highlighting: bool = False,
                     offset: int = 0,
                     limit: int = 10,
                     biolink_types: Optional[List[str]] = None,
                     only_prefixes: Optional[str] = None,
                     exclude_prefixes: Optional[str] = None,
                     only_taxa: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Look up multiple entities by name using the bulk lookup API.
    
    Args:
        strings: List of search terms
        autocomplete: Enable autocomplete/partial matching (default: False)
        highlighting: Enable search term highlighting (default: False)
        offset: Number of results to skip for pagination (default: 0)
        limit: Maximum number of results per string (default: 10)
        biolink_types: Filter by Biolink entity types (e.g., ['SmallMolecule', 'Gene'])
        only_prefixes: Only include results from these namespaces (comma-separated)
        exclude_prefixes: Exclude results from these namespaces (comma-separated)
        only_taxa: Only include results from these taxa (comma-separated, e.g., 'NCBITaxon:9606')
    
    Returns:
        Dictionary mapping each input string to its list of matching entities
        
    Raises:
        APIException: If the API request fails
    """
    url = "https://name-resolution-sri-dev.apps.renci.org/bulk-lookup"
    
    payload = {
        "strings": strings,
        "autocomplete": autocomplete,
        "highlighting": highlighting,
        "offset": offset,
        "limit": limit,
        "biolink_types": biolink_types or [],
        "only_prefixes": only_prefixes or "",
        "exclude_prefixes": exclude_prefixes or "",
        "only_taxa": only_taxa or ""
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIException(f"Name resolver bulk lookup API request failed: {e}")
    except json.JSONDecodeError as e:
        raise APIException(f"Failed to parse bulk lookup API response: {e}")


def get_exact_matches(lookup_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Return all lookup results without filtering by score.
    
    The previous implementation filtered by highest score, but this was eliminating
    legitimate ambiguous matches where multiple entities had the same high score.
    Now we return all results and let the ambiguity detection logic handle multiple matches.
    
    Args:
        lookup_results: Results from lookup_names function
    
    Returns:
        All lookup results (no longer filtering by score)
    """
    return lookup_results if lookup_results else []