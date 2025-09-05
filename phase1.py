#!/usr/bin/env python3
"""
Phase 1 Edge Classification - Standalone Functions Version

This module contains functions for classifying edges based on entity identification
and ambiguity detection using various APIs (Node Normalizer, Name Resolver, etc.).
"""

import argparse
import json
import os
import re
import tempfile
import time
import uuid
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

from api_functions import (
    batch_get_normalized_nodes, 
    batch_get_synonyms, 
    lookup_names,
    bulk_lookup_names,
    get_exact_matches,
    APIException
)


def find_synonyms_in_text(text: str, synonyms: List[str]) -> List[str]:
    """
    Find which synonyms appear in the given text.
    
    Args:
        text: Text to search in
        synonyms: List of possible synonyms
    
    Returns:
        List of synonyms found in text
    """
    if not text or not synonyms:
        return []
    
    found_synonyms = []
    text_lower = text.lower()
    
    for synonym in synonyms:
        if not synonym:
            continue
        
        synonym_lower = synonym.lower()
        
        # Look for exact word matches (not just substring matches)
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(synonym_lower) + r'\b'
        if re.search(pattern, text_lower):
            found_synonyms.append(synonym)
    
    return found_synonyms


def format_lookup_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a lookup result for storage in debug info.
    
    Args:
        result: Raw result from lookup_names API
        
    Returns:
        Formatted result dictionary with limited fields
    """
    return {
        'curie': result.get('curie', 'N/A'),
        'label': result.get('label', 'N/A'),
        'taxa': result.get('taxa', []),
        'score': result.get('score', 0),
        'synonyms': result.get('synonyms', [])[:10],  # Limit synonyms for storage
        'types': [t.replace('biolink:', '') for t in result.get('types', [])][:3]  # Show top 3 types
    }


def write_edge_result(edge: Dict[str, Any], classification: str, output_files: Dict[str, Any],
                     nodes: Dict[str, Any] = None, debug_info: Dict[str, Any] = None) -> None:
    """
    Write edge result to appropriate output file.
    
    Args:
        edge: Edge dictionary
        classification: Classification result ('good', 'bad', 'ambiguous')
        output_files: Dictionary with output file handles
        nodes: Node data for entity names
        debug_info: Optional debug information including found synonyms
    """
    # Add classification to edge data
    result_edge = edge.copy()
    result_edge['qc_classification'] = classification
    result_edge['qc_phase'] = 'phase1_entity_identification'
    
    # Add entity names for webapp display
    if nodes:
        subject_node = nodes.get(edge['subject'])
        object_node = nodes.get(edge['object'])
        
        result_edge['subject_name'] = subject_node.get('name', edge['subject']) if subject_node else edge['subject']
        result_edge['object_name'] = object_node.get('name', edge['object']) if object_node else edge['object']
    else:
        result_edge['subject_name'] = edge['subject']
        result_edge['object_name'] = edge['object']
    
    # Add debug information for synonym highlighting
    if debug_info:
        result_edge['qc_debug'] = debug_info
    
    # Add a unique edge identifier for debugging
    if 'edge_id' not in result_edge:
        result_edge['edge_id'] = str(uuid.uuid4())
    
    # Write to appropriate output file
    output_key = f'{classification}_edges'
    if output_key in output_files:
        output_files[output_key].write(json.dumps(result_edge) + '\n')
        output_files[output_key].flush()


def check_entity_in_text_with_cache(text: str, synonyms: List[str], 
                                   lookup_cache: Dict[str, List[Dict[str, Any]]], 
                                   debug_info: Dict[str, Any], entity_role: str) -> bool:
    """
    Check if entity is found in text using synonyms and lookup cache.
    
    Args:
        text: Text to search in
        synonyms: Entity synonyms
        lookup_cache: Pre-computed lookup results
        debug_info: Debug info dictionary to update
        entity_role: 'subject' or 'object' for debug labeling
        
    Returns:
        True if entity found in text
    """
    found_synonyms = find_synonyms_in_text(text, synonyms)
    debug_info[f'{entity_role}_synonyms_found'] = found_synonyms
    
    if not found_synonyms:
        return False
    
    # Check for ambiguous matches among found synonyms
    found_ambiguous = []
    lookup_data = {}
    
    for synonym in found_synonyms:
        if synonym in lookup_cache:
            lookup_results = lookup_cache[synonym]
            lookup_data[synonym] = [format_lookup_result(result) for result in lookup_results[:5]]
            
            # Check if this synonym has multiple distinct matches (ambiguous)
            if len(lookup_results) > 1:
                found_ambiguous.append(synonym)
    
    debug_info[f'{entity_role}_ambiguous'] = len(found_ambiguous) > 0
    debug_info[f'{entity_role}_lookup_data'] = lookup_data
    
    return True


def check_ambiguous_matches_with_cache(synonyms: List[str], 
                                     lookup_cache: Dict[str, List[Dict[str, Any]]]) -> Tuple[bool, List[str], Dict[str, List[Dict[str, Any]]]]:
    """
    Check if any synonyms have ambiguous matches using cached lookup results.
    
    Args:
        synonyms: List of synonyms to check
        lookup_cache: Pre-computed lookup results for synonyms
        
    Returns:
        Tuple of (has_ambiguous, ambiguous_synonyms, lookup_results)
    """
    ambiguous_synonyms = []
    lookup_results = {}
    
    for synonym in synonyms:
        if synonym in lookup_cache:
            results = lookup_cache[synonym]
            lookup_results[synonym] = results
            
            # Check for multiple matches (potential ambiguity)
            if len(results) > 1:
                ambiguous_synonyms.append(synonym)
    
    has_ambiguous = len(ambiguous_synonyms) > 0
    return has_ambiguous, ambiguous_synonyms, lookup_results


def classify_edge(edge: Dict[str, Any], 
                 lookup_cache: Dict[str, List[Dict[str, Any]]], 
                 normalized_data: Dict[str, Any],
                 synonyms_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Classify a single edge as good, bad, or ambiguous.
    
    Args:
        edge: Edge dictionary with subject, object, sentences
        lookup_cache: Pre-computed lookup results for all synonyms
        normalized_data: Entity normalization data
        synonyms_data: Entity synonym data
    
    Returns:
        Tuple of (classification, debug_info)
    """
    debug_info = {
        'subject_curie': edge.get('subject', 'N/A'),
        'object_curie': edge.get('object', 'N/A'),
        'edge_text': edge.get('sentences', '')
    }
    
    # Get entity data
    subject_entity = edge.get('subject')
    object_entity = edge.get('object')
    
    # Check if we have synonyms for both entities
    if subject_entity not in synonyms_data:
        debug_info['reason'] = f'Missing synonyms for subject or object'
        return 'bad', debug_info
    
    if object_entity not in synonyms_data:
        debug_info['reason'] = f'Missing synonyms for subject or object'
        return 'bad', debug_info
    
    subject_synonyms = synonyms_data[subject_entity].get('names', [])
    object_synonyms = synonyms_data[object_entity].get('names', [])
    
    # Get text for analysis
    text = edge.get('sentences', '')
    
    # Check for valid text
    if not text or text.strip() == '' or text.strip().upper() == 'NA':
        debug_info['reason'] = 'No supporting text available'
        return 'bad', debug_info
    
    # Check if both entities are found in text
    subject_found = check_entity_in_text_with_cache(
        text, subject_synonyms, lookup_cache, debug_info, 'subject'
    )
    object_found = check_entity_in_text_with_cache(
        text, object_synonyms, lookup_cache, debug_info, 'object'
    )
    
    # If either entity not found, classify as bad
    if not subject_found:
        debug_info['reason'] = 'Subject not found in text'
        return 'bad', debug_info
    
    if not object_found:
        debug_info['reason'] = 'Object not found in text'
        return 'bad', debug_info
    
    # Check for ambiguous matches
    all_found_synonyms = debug_info.get('subject_synonyms_found', []) + debug_info.get('object_synonyms_found', [])
    
    has_ambiguous = False
    for synonym in all_found_synonyms:
        if synonym in lookup_cache and len(lookup_cache[synonym]) > 1:
            has_ambiguous = True
            break
    
    if has_ambiguous:
        debug_info['reason'] = 'Ambiguous entity matches found'
        return 'ambiguous', debug_info
    
    # If we get here, both entities found and no ambiguity
    debug_info['reason'] = 'Both entities found unambiguously in text'
    return 'good', debug_info


def create_output_files(output_dir: str) -> Dict[str, Any]:
    """
    Create and return output file handles.
    
    Args:
        output_dir: Output directory path
        
    Returns:
        Dictionary of output file handles
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    output_files = {
        'good_edges': open(output_path / "good_edges.jsonl", 'w'),
        'bad_edges': open(output_path / "bad_edges.jsonl", 'w'), 
        'ambiguous_edges': open(output_path / "ambiguous_edges.jsonl", 'w')
    }
    
    return output_files


def close_output_files(output_files: Dict[str, Any]) -> None:
    """Close all output file handles."""
    for f in output_files.values():
        f.close()


# ============================================================================
# 4-STAGE PIPELINE FUNCTIONS
# ============================================================================

def stage1_entity_collection_and_normalization(edges_file: str, max_edges: int = None) -> Tuple[List[str], Dict[str, Any]]:
    """
    Stage 1: Entity Collection & Normalization
    
    Collect unique entities from edges file and normalize them using Node Normalizer API.
    
    Args:
        edges_file: Path to JSONL file with edges
        max_edges: Maximum edges to process (None for all)
        
    Returns:
        Tuple of (entities_list, normalized_data_dict)
    """
    print("=== STAGE 1: Entity Collection & Normalization ===")
    
    # Collect unique entities by streaming through edges
    print("Collecting unique entities by streaming through edges...")
    start_time = time.time()
    entities = set()
    edge_count = 0
    
    with open(edges_file, 'r') as f:
        for line in f:
            if line.strip():
                edge = json.loads(line)
                entities.add(edge.get('subject'))
                entities.add(edge.get('object'))
                edge_count += 1
                
                if max_edges and edge_count >= max_edges:
                    break
    
    entities = list(entities)
    entities_time = time.time() - start_time
    print(f"Found {len(entities)} unique entities from {edge_count} edges")
    print(f"Entity collection completed in {entities_time:.2f} seconds")
    
    # Normalize entities
    print("Normalizing entities...")
    start_time = time.time()
    normalized_data = batch_get_normalized_nodes(entities)
    normalize_time = time.time() - start_time
    print(f"Entity normalization completed in {normalize_time:.2f} seconds")
    
    return entities, normalized_data


def stage2_synonym_retrieval(normalized_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage 2: Synonym Retrieval
    
    Get synonyms for normalized entities using Name Resolver API.
    
    Args:
        normalized_data: Entity normalization data from stage 1
        
    Returns:
        Dictionary of synonym data
    """
    print("=== STAGE 2: Synonym Retrieval ===")
    
    # Get synonyms for preferred entities
    print("Getting synonyms...")
    start_time = time.time()
    preferred_entities = [data['id']['identifier'] for data in normalized_data.values() if data]
    synonyms_data = batch_get_synonyms(preferred_entities)
    synonyms_time = time.time() - start_time
    print(f"Synonym retrieval completed in {synonyms_time:.2f} seconds")
    
    return synonyms_data


def stage3_text_matching_and_lookup(edge: Dict[str, Any], 
                                   synonyms_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Stage 3: Text Matching & Lookup
    
    Find which synonyms from Stage 2 appear in the edge text, then perform reverse lookups
    on those found synonyms to prepare for ambiguity evaluation in Stage 4.
    
    Args:
        edge: Edge dictionary with subject, object, sentences
        synonyms_data: Synonym data from stage 2
        
    Returns:
        Lookup cache dictionary mapping found synonyms to their lookup results
    """
    print("=== STAGE 3: Text Matching & Lookup ===")
    
    # Get the supporting text
    text = edge.get('sentences', '')
    if not text or text.strip() in ['', 'NA']:
        print("No supporting text available")
        return {}
    
    # Find synonyms that appear in text
    print("Finding synonyms in supporting text...")
    start_time = time.time()
    found_synonyms = set()
    
    # Check each entity's synonyms against the text
    for entity_id, entity_synonyms in synonyms_data.items():
        if 'names' in entity_synonyms:
            for synonym in entity_synonyms['names']:
                if synonym and synonym.strip() and synonym.lower() in text.lower():
                    found_synonyms.add(synonym)
    
    print(f"Found {len(found_synonyms)} synonyms in text: {list(found_synonyms)[:5]}...")
    
    if not found_synonyms:
        print("No synonyms found in text")
        return {}
    
    # Execute reverse lookups for found synonyms with proper filtering
    print("Performing reverse lookups for found synonyms...")
    lookup_cache = {}
    
    # Group synonyms by their entity types for proper biolink filtering
    for synonym in found_synonyms:
        # Find which entity this synonym belongs to 
        entity_types = []
        for entity_id, entity_synonyms in synonyms_data.items():
            if 'names' in entity_synonyms and synonym in entity_synonyms['names']:
                entity_types = entity_synonyms.get('types', [])
                break
        
        # Determine biolink type and taxon filtering
        biolink_types = []
        only_taxa = []
        
        # Map entity types to biolink types for lookup
        for entity_type in entity_types:
            if 'Gene' in entity_type or 'gene' in entity_type.lower():
                biolink_types.append('Gene')
                only_taxa.append('NCBITaxon:9606')  # Human taxon for genes
            elif 'SmallMolecule' in entity_type or 'Chemical' in entity_type:
                biolink_types.append('SmallMolecule')
            elif 'Disease' in entity_type:
                biolink_types.append('Disease')
        
        # Execute lookup with proper filtering
        if biolink_types:
            only_taxa_str = ','.join(only_taxa) if only_taxa else ""
            results = bulk_lookup_names([synonym], 
                                      biolink_types=biolink_types,
                                      only_taxa=only_taxa_str,
                                      limit=20)
        else:
            # Fallback: lookup without filtering
            results = bulk_lookup_names([synonym], limit=20)
        
        # Filter to only perfect matches (exact synonym match, case insensitive)
        if synonym in results:
            perfect_matches = []
            for result in results[synonym]:
                synonyms_list = result.get('synonyms', [])
                label = result.get('label', '')
                
                # Check if synonym appears exactly in synonyms list or as label (case insensitive)
                has_exact_match = (
                    synonym in synonyms_list or 
                    synonym.upper() in [s.upper() for s in synonyms_list] or
                    synonym.upper() == label.upper()
                )
                
                if has_exact_match:
                    perfect_matches.append(result)
            
            lookup_cache[synonym] = perfect_matches
    
    lookup_time = time.time() - start_time
    print(f"Text matching and lookup completed in {lookup_time:.2f} seconds")
    
    return lookup_cache


def stage4_classification_logic(edge: Dict[str, Any], 
                               lookup_cache: Dict[str, List[Dict[str, Any]]],
                               normalized_data: Dict[str, Any],
                               synonyms_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Stage 4: Classification Logic
    
    Classify a single edge as good, bad, or ambiguous.
    This is the existing classify_edge function renamed for consistency.
    
    Args:
        edge: Edge dictionary with subject, object, sentences
        lookup_cache: Pre-computed lookup results from stage 3
        normalized_data: Entity normalization data from stage 1
        synonyms_data: Entity synonym data from stage 2
        
    Returns:
        Tuple of (classification, debug_info)
    """
    return classify_edge(edge, lookup_cache, normalized_data, synonyms_data)


# ============================================================================
# MAIN PIPELINE FUNCTION
# ============================================================================

def run_streaming(edges_file: str, nodes_file: str, output_dir: str = "output", 
                 batch_size: int = 1000, max_edges: int = None) -> None:
    """
    Run edge classification in streaming mode with batching.
    
    Args:
        edges_file: Path to JSONL file with edges
        nodes_file: Path to JSONL file with nodes
        output_dir: Directory for output files
        batch_size: Number of edges per batch
        max_edges: Maximum edges to process (None for all)
    """
    print("Starting Phase 1 edge classification (streaming mode)...")
    overall_start = time.time()
    
    # Load nodes for entity name lookup
    print("Loading nodes...")
    start_time = time.time()
    nodes = {}
    with open(nodes_file, 'r') as f:
        for line in f:
            if line.strip():
                node = json.loads(line)
                nodes[node['id']] = node
    
    nodes_time = time.time() - start_time
    print(f"Loaded {len(nodes)} nodes")
    print(f"Node loading completed in {nodes_time:.2f} seconds")
    
    # Clear existing output files and create new ones
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for filename in ["good_edges.jsonl", "bad_edges.jsonl", "ambiguous_edges.jsonl"]:
        filepath = output_path / filename
        if filepath.exists():
            filepath.unlink()
    
    # Execute Stages 1-2 globally (entity collection and synonyms)
    entities, normalized_data = stage1_entity_collection_and_normalization(edges_file, max_edges)
    synonyms_data = stage2_synonym_retrieval(normalized_data)
    # Stages 3-4 are executed per-edge in the streaming batch processing
    
    # Process edges in streaming batches
    print(f"Processing edges in streaming batches of {batch_size}...")
    
    output_files = create_output_files(output_dir)
    
    edge_count = 0
    batch_num = 1
    current_batch = []
    
    start_time = time.time()
    
    with open(edges_file, 'r') as f:
        for line in f:
            if line.strip():
                edge = json.loads(line)
                current_batch.append(edge)
                edge_count += 1
                
                # Process batch when full or at end
                if len(current_batch) >= batch_size or (max_edges and edge_count >= max_edges):
                    is_final = (max_edges and edge_count >= max_edges)
                    
                    batch_start = time.time()
                    process_streaming_batch(current_batch, nodes, normalized_data, synonyms_data, output_files)
                    batch_time = time.time() - batch_start
                    
                    rate = len(current_batch) / batch_time if batch_time > 0 else 0
                    final_text = " (final)" if is_final else ""
                    print(f"  Batch {batch_num}{final_text}: processed {len(current_batch)} edges in {batch_time:.3f}s ({rate:.1f} edges/sec) - Total: {edge_count}/{edge_count}")
                    
                    current_batch = []
                    batch_num += 1
                
                if max_edges and edge_count >= max_edges:
                    break
    
    # Process remaining edges if any
    if current_batch:
        batch_start = time.time()
        process_streaming_batch(current_batch, nodes, normalized_data, synonyms_data, output_files)
        batch_time = time.time() - batch_start
        rate = len(current_batch) / batch_time if batch_time > 0 else 0
        print(f"  Final batch: processed {len(current_batch)} edges in {batch_time:.3f}s ({rate:.1f} edges/sec)")
    
    process_time = time.time() - start_time
    print(f"Edge processing completed in {process_time:.2f} seconds")
    
    # Close output files
    close_output_files(output_files)
    
    # Final statistics
    total_time = time.time() - overall_start
    rate = edge_count / total_time if total_time > 0 else 0
    
    print(f"Total runtime: {total_time:.2f} seconds")
    print(f"Processing rate: {rate:.1f} edges/second")
    
    # Count results
    output_files_paths = {
        'good_edges': output_path / "good_edges.jsonl",
        'bad_edges': output_path / "bad_edges.jsonl",
        'ambiguous_edges': output_path / "ambiguous_edges.jsonl"
    }
    
    counts = {}
    for category, filepath in output_files_paths.items():
        count = 0
        if filepath.exists():
            with open(filepath, 'r') as f:
                for line in f:
                    if line.strip():
                        count += 1
        counts[category.replace('_edges', '')] = count
    
    print("\nClassification Summary:")
    for category, count in counts.items():
        if count > 0:
            print(f"{category.title()} edges: {count}")
    print(f"Total: {sum(counts.values())}")
    
    print("\nTiming Breakdown:")
    print(f"  Node loading: {nodes_time:.2f}s")
    print(f"  Entity collection: {entities_time:.2f}s") 
    print(f"  Entity normalization: {normalize_time:.2f}s")
    print(f"  Synonym retrieval: {synonyms_time:.2f}s")
    print(f"  Edge processing: {process_time:.2f}s")
    print(f"  Total: {total_time:.2f}s")
    
    print(f"\nOutput files created:")
    for category, filepath in output_files_paths.items():
        print(f"{category.title().replace('_', ' ')}: {filepath}")


def process_streaming_batch(batch_edges: List[Dict[str, Any]], nodes: Dict[str, Any], 
                          normalized_data: Dict[str, Any], synonyms_data: Dict[str, Any],
                          output_files: Dict[str, Any]) -> None:
    """Process a batch of edges in streaming mode."""
    
    # Collect all synonyms from this batch
    synonym_groups = collect_synonyms_from_batch(batch_edges, synonyms_data)
    
    # Execute bulk lookups
    lookup_cache = execute_bulk_lookups(synonym_groups)
    
    # Classify each edge in the batch using Stage 4
    for edge in batch_edges:
        classification, debug_info = stage4_classification_logic(edge, lookup_cache, normalized_data, synonyms_data)
        write_edge_result(edge, classification, output_files, nodes, debug_info)


def collect_synonyms_from_batch(batch_edges: List[Dict[str, Any]], 
                               synonyms_data: Dict[str, Any]) -> Dict[str, Set[str]]:
    """Collect all synonyms needed for a batch of edges."""
    synonym_groups = defaultdict(set)
    
    for edge in batch_edges:
        subject_entity = edge.get('subject')
        object_entity = edge.get('object')
        
        if subject_entity in synonyms_data:
            subject_synonyms = synonyms_data[subject_entity].get('names', [])
            synonym_groups['batch_synonyms'].update(subject_synonyms)
        
        if object_entity in synonyms_data:
            object_synonyms = synonyms_data[object_entity].get('names', [])
            synonym_groups['batch_synonyms'].update(object_synonyms)
    
    return synonym_groups


def execute_bulk_lookups(synonym_groups: Dict[str, Set[str]]) -> Dict[str, List[Dict[str, Any]]]:
    """Execute bulk lookups for synonym groups."""
    lookup_cache = {}
    
    for group_name, synonyms in synonym_groups.items():
        if synonyms:
            synonyms_list = list(synonyms)
            group_results = bulk_lookup_names(synonyms_list, limit=20)
            lookup_cache.update(group_results)
    
    return lookup_cache


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="Phase 1 Edge Classification")
    parser.add_argument("edges_file", help="Path to edges JSONL file")
    parser.add_argument("nodes_file", help="Path to nodes JSONL file") 
    parser.add_argument("--output", default="output", help="Output directory (default: output)")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for processing")
    parser.add_argument("--max-edges", type=int, help="Maximum edges to process")
    
    args = parser.parse_args()
    
    run_streaming(args.edges_file, args.nodes_file, args.output, args.batch_size, args.max_edges)


if __name__ == "__main__":
    main()