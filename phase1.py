"""
Phase 1 implementation for TMKP edge quality control.

This module handles the first phase of QC which focuses on entity identification:
1. Load edges and collect all unique entities (subjects and objects)
2. Normalize entities using node normalizer API
3. Get synonyms for all preferred identifiers  
4. For each edge, check if synonyms appear in the supporting text
5. Classify edges as good, bad, or ambiguous based on entity identification
"""

import json
import os
import re
import time
from typing import Dict, List, Set, Tuple, Any
from pathlib import Path
import uuid
from collections import defaultdict

from api_functions import (
    batch_get_normalized_nodes, 
    batch_get_synonyms, 
    lookup_names,
    bulk_lookup_names,
    get_exact_matches,
    APIException
)


class EdgeClassifier:
    """Main class for edge classification in Phase 1."""
    
    def __init__(self, edges_file: str, nodes_file: str, output_dir: str = "output"):
        self.edges_file = edges_file
        self.nodes_file = nodes_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Data storage (only used by write_edge_result for entity names)
        self.nodes = {}
        
        # Output files
        self.good_edges_file = self.output_dir / "good_edges.jsonl"
        self.bad_edges_file = self.output_dir / "bad_edges.jsonl" 
        self.ambiguous_edges_file = self.output_dir / "ambiguous_edges.jsonl"
        
        # Clear existing output files
        for output_file in [self.good_edges_file, self.bad_edges_file, self.ambiguous_edges_file]:
            if output_file.exists():
                output_file.unlink()
    
    
    def find_synonyms_in_text(self, text: str, synonyms: List[str]) -> List[str]:
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
    
    def _format_lookup_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
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
    
    
    
    def write_edge_result(self, edge: Dict[str, Any], classification: str, debug_info: Dict[str, Any] = None) -> None:
        """
        Write edge result to appropriate output file.
        
        Args:
            edge: Edge dictionary
            classification: Classification result ('good', 'bad', 'ambiguous')
            debug_info: Optional debug information including found synonyms
        """
        # Add classification to edge data
        result_edge = edge.copy()
        result_edge['qc_classification'] = classification
        result_edge['qc_phase'] = 'phase1_entity_identification'
        
        # Add entity names for webapp display
        subject_node = self.nodes.get(edge['subject'])
        object_node = self.nodes.get(edge['object'])
        
        result_edge['subject_name'] = subject_node.get('name', edge['subject']) if subject_node else edge['subject']
        result_edge['object_name'] = object_node.get('name', edge['object']) if object_node else edge['object']
        
        # Add debug information for synonym highlighting
        if debug_info:
            result_edge['qc_debug'] = debug_info
        
        # Choose output file
        if classification == 'good':
            output_file = self.good_edges_file
        elif classification == 'bad':
            output_file = self.bad_edges_file
        else:  # ambiguous
            output_file = self.ambiguous_edges_file
        
        # Write to file
        with open(output_file, 'a') as f:
            f.write(json.dumps(result_edge) + '\n')
    
    def collect_all_synonyms_from_batch(self, edges: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """
        Collect all unique synonyms from a batch of edges, grouped by biolink type.
        
        Args:
            edges: List of edges to process
            
        Returns:
            Dictionary mapping biolink types to sets of unique synonyms
        """
        synonym_groups = defaultdict(set)
        
        for edge in edges:
            # Get edge text
            edge_text = edge.get('sentences', '')
            if not edge_text or edge_text == 'NA':
                continue
                
            # Extract synonyms from text (same logic as find_synonyms_in_text)
            synonyms = set()
            for curie in [edge.get('subject'), edge.get('object')]:
                if curie and curie in self.synonyms_data:
                    synonym_list = self.synonyms_data[curie]
                    if synonym_list:
                        synonyms.update(synonym_list)
            
            # Find synonyms in text and group by biolink type
            for synonym in synonyms:
                if self.find_synonyms_in_text(edge_text, [synonym]):
                    # For now, we'll use a default group since we don't have biolink types
                    # TODO: Enhance this to actually group by biolink type when available
                    synonym_groups['default'].add(synonym)
        
        return synonym_groups
    
    def execute_bulk_lookups(self, synonym_groups: Dict[str, Set[str]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute bulk lookups for grouped synonyms and return cached results.
        
        Args:
            synonym_groups: Dictionary mapping biolink types to synonym sets
            
        Returns:
            Dictionary mapping synonyms to their lookup results
        """
        lookup_cache = {}
        
        for group_type, synonyms in synonym_groups.items():
            if not synonyms:
                continue
                
            synonym_list = list(synonyms)
            print(f"Executing bulk lookup for {len(synonym_list)} {group_type} synonyms")
            
            try:
                # Execute bulk lookup
                bulk_results = bulk_lookup_names(synonym_list, limit=10)
                
                # Store results in cache
                for synonym, results in bulk_results.items():
                    lookup_cache[synonym] = results
                    
            except APIException as e:
                print(f"Warning: Bulk lookup failed for {group_type} group: {e}")
                # Fallback to individual lookups for this group
                for synonym in synonyms:
                    try:
                        lookup_cache[synonym] = lookup_names(synonym, limit=10)
                    except APIException:
                        print(f"Warning: Could not lookup synonym '{synonym}'")
                        lookup_cache[synonym] = []
        
        return lookup_cache
    
    
    
    def classify_edge(self, edge: Dict[str, Any], 
                      lookup_cache: Dict[str, List[Dict[str, Any]]],
                      normalized_data: Dict[str, Any],
                      synonyms_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Classify an edge using cached lookup results instead of making API calls.
        
        Args:
            edge: Edge to classify
            lookup_cache: Cached lookup results
            normalized_data: Normalized entity data
            synonyms_data: Synonym data
            
        Returns:
            Tuple of (classification, debug_info)
        """
        # This is similar to classify_edge but uses lookup_cache instead of calling lookup_names
        debug_info = {
            'subject_curie': edge.get('subject'),
            'object_curie': edge.get('object'),
            'edge_text': edge.get('sentences', 'NA')
        }
        
        # Check if we have sentences
        if not edge.get('sentences') or edge.get('sentences') == 'NA':
            debug_info['reason'] = 'No supporting text available'
            return 'bad', debug_info
            
        # Get normalized CURIEs first
        subject_data = normalized_data.get(edge.get('subject'), {})
        object_data = normalized_data.get(edge.get('object'), {})
        
        if not subject_data or not object_data:
            debug_info['reason'] = 'Missing normalized data for subject or object'
            return 'bad', debug_info
            
        subject_preferred = subject_data.get('id', {}).get('identifier') if subject_data else None
        object_preferred = object_data.get('id', {}).get('identifier') if object_data else None
        
        if not subject_preferred or not object_preferred:
            debug_info['reason'] = 'Missing preferred identifiers for subject or object'
            return 'bad', debug_info
        
        # Get entity synonyms using preferred CURIEs
        subject_synonyms_data = synonyms_data.get(subject_preferred, {})
        object_synonyms_data = synonyms_data.get(object_preferred, {})
        
        subject_synonyms = subject_synonyms_data.get('names', []) if subject_synonyms_data else []
        object_synonyms = object_synonyms_data.get('names', []) if object_synonyms_data else []
        
        if not subject_synonyms or not object_synonyms:
            debug_info['reason'] = 'Missing synonyms for subject or object'
            return 'bad', debug_info
        
        # Check subject and object using cached lookups
        subject_found = self._check_entity_in_text_with_cache(
            edge.get('sentences'), subject_synonyms, lookup_cache, debug_info, 'subject')
        object_found = self._check_entity_in_text_with_cache(
            edge.get('sentences'), object_synonyms, lookup_cache, debug_info, 'object')
        
        # Check for ambiguity first (like in the original classify_edge method)
        subject_ambiguous = debug_info.get('subject_ambiguous', False)
        object_ambiguous = debug_info.get('object_ambiguous', False)
        
        if subject_ambiguous or object_ambiguous:
            return 'ambiguous', debug_info
        
        # Classification logic
        if subject_found and object_found:
            return 'good', debug_info
        elif not subject_found and not object_found:
            debug_info['reason'] = 'Neither subject nor object found in text'
            return 'bad', debug_info
        else:
            if not subject_found:
                debug_info['reason'] = 'Subject not found in text'
            else:
                debug_info['reason'] = 'Object not found in text'
            return 'bad', debug_info
    
    def _check_entity_in_text_with_cache(self, text: str, synonyms: List[str], 
                                        lookup_cache: Dict[str, List[Dict[str, Any]]], 
                                        debug_info: Dict[str, Any], entity_type: str) -> bool:
        """
        Check if an entity is found in text using cached lookup results.
        Returns True if found (regardless of ambiguity), False if not found.
        Ambiguity is stored separately in debug_info.
        """
        found_synonyms = self.find_synonyms_in_text(text, synonyms)
        if not found_synonyms:
            debug_info[f'{entity_type}_synonyms_found'] = []
            debug_info[f'{entity_type}_ambiguous'] = False
            return False
        
        # Use the enhanced ambiguity logic with cached results
        is_ambiguous, filtered_lookup_data = self.check_ambiguous_matches_with_cache(found_synonyms, lookup_cache)
        
        # Store debug information
        debug_info[f'{entity_type}_synonyms_found'] = found_synonyms
        debug_info[f'{entity_type}_ambiguous'] = is_ambiguous
        debug_info[f'{entity_type}_lookup_data'] = filtered_lookup_data
        
        # Return True if synonyms found (regardless of ambiguity)
        # Ambiguity will be handled in the main classification logic
        return True
    
    def check_ambiguous_matches_with_cache(self, synonyms: List[str], 
                                          lookup_cache: Dict[str, List[Dict[str, Any]]]) -> Tuple[bool, Dict[str, List[Dict[str, Any]]]]:
        """
        Enhanced ambiguity checking using cached lookup results with preferred name logic.
        
        Args:
            synonyms: List of synonyms found in text
            lookup_cache: Cached lookup results
            
        Returns:
            Tuple of (is_ambiguous, filtered_lookup_data)
        """
        lookup_data = {}
        is_ambiguous = False
        
        for synonym in synonyms:
            # Get cached lookup results
            lookup_results = lookup_cache.get(synonym, [])
            if not lookup_results:
                continue
                
            # Get exact matches
            exact_matches = get_exact_matches(lookup_results)
            lookup_data[synonym] = exact_matches
            
            # Enhanced ambiguity logic: prefer matches where synonym is preferred name
            if len(exact_matches) > 1:
                # Check if exactly one match has this synonym as preferred name
                preferred_matches = []
                for match in exact_matches:
                    # Check if the synonym matches the preferred label (case-insensitive)
                    preferred_label = match.get('label', '').lower()
                    if synonym.lower() == preferred_label:
                        preferred_matches.append(match)
                
                # If exactly one match has the synonym as preferred name, it's not ambiguous
                if len(preferred_matches) == 1:
                    # Keep only the preferred match in lookup data
                    lookup_data[synonym] = preferred_matches
                else:
                    # Still ambiguous - either 0 or multiple preferred matches
                    is_ambiguous = True
        
        return is_ambiguous, lookup_data
    

    
    
    def run_streaming(self, batch_size: int = 1000, max_edges: int = None) -> None:
        """
        Run Phase 1 classification using streaming processing.
        Processes edges in chunks without loading the entire dataset into memory.
        
        Args:
            batch_size: Number of edges to process in each streaming batch
            max_edges: Maximum number of edges to process (for testing)
        """
        overall_start_time = time.time()
        print("Starting Phase 1 edge classification (streaming mode)...")
        
        # Only load nodes into memory (much smaller - ~400MB vs ~2GB)
        start_time = time.time()
        print("Loading nodes...")
        nodes = {}
        with open(self.nodes_file, 'r') as f:
            for line in f:
                node = json.loads(line.strip())
                nodes[node['id']] = node
        print(f"Loaded {len(nodes)} nodes")
        load_time = time.time() - start_time
        print(f"Node loading completed in {load_time:.2f} seconds")
        
        # Get all unique entities by streaming through edges once
        start_time = time.time()
        print("Collecting unique entities by streaming through edges...")
        entities = set()
        total_edges_count = 0
        
        with open(self.edges_file, 'r') as f:
            for i, line in enumerate(f):
                if max_edges and i >= max_edges:
                    break
                edge = json.loads(line.strip())
                entities.add(edge['subject'])
                entities.add(edge['object'])
                total_edges_count += 1
        
        entities = list(entities)
        collect_time = time.time() - start_time
        print(f"Found {len(entities)} unique entities from {total_edges_count} edges")
        print(f"Entity collection completed in {collect_time:.2f} seconds")
        
        # Normalize entities and get synonyms
        start_time = time.time()
        print("Normalizing entities...")
        normalized_data = batch_get_normalized_nodes(entities)
        normalize_time = time.time() - start_time
        print(f"Entity normalization completed in {normalize_time:.2f} seconds")
        
        start_time = time.time()
        print("Getting synonyms...")
        preferred_entities = [data['id']['identifier'] for data in normalized_data.values() if data]
        synonyms_data = batch_get_synonyms(preferred_entities)
        synonyms_time = time.time() - start_time
        print(f"Synonym retrieval completed in {synonyms_time:.2f} seconds")
        
        # Stream process edges in batches
        start_time = time.time()
        print(f"Processing edges in streaming batches of {batch_size}...")
        
        # Initialize classification counts and output files
        classification_counts = defaultdict(int)
        output_files = self._create_output_files()
        
        processed_edges = 0
        batch_num = 0
        
        with open(self.edges_file, 'r') as f:
            batch_edges = []
            
            for i, line in enumerate(f):
                if max_edges and i >= max_edges:
                    break
                    
                edge = json.loads(line.strip())
                edge['edge_id'] = str(uuid.uuid4())
                batch_edges.append(edge)
                
                # Process batch when full
                if len(batch_edges) >= batch_size:
                    batch_num += 1
                    batch_start_time = time.time()
                    
                    # Process this batch using the batched lookup approach
                    batch_results = self._process_streaming_batch(
                        batch_edges, nodes, normalized_data, synonyms_data
                    )
                    
                    # Update counts and write results
                    for classification in batch_results:
                        classification_counts[classification] += batch_results[classification]
                    
                    processed_edges += len(batch_edges)
                    batch_time = time.time() - batch_start_time
                    
                    print(f"  Batch {batch_num}: processed {len(batch_edges)} edges in {batch_time:.3f}s "
                          f"({len(batch_edges)/batch_time:.1f} edges/sec) - "
                          f"Total: {processed_edges}/{total_edges_count}")
                    
                    # Clear batch to free memory
                    batch_edges = []
            
            # Process final partial batch
            if batch_edges:
                batch_num += 1
                batch_start_time = time.time()
                
                batch_results = self._process_streaming_batch(
                    batch_edges, nodes, normalized_data, synonyms_data
                )
                
                for classification in batch_results:
                    classification_counts[classification] += batch_results[classification]
                
                processed_edges += len(batch_edges)
                batch_time = time.time() - batch_start_time
                
                print(f"  Batch {batch_num} (final): processed {len(batch_edges)} edges in {batch_time:.3f}s "
                      f"({len(batch_edges)/batch_time:.1f} edges/sec) - "
                      f"Total: {processed_edges}/{total_edges_count}")
        
        # Close output files
        for f in output_files.values():
            f.close()
        
        processing_time = time.time() - start_time
        total_time = time.time() - overall_start_time
        
        print(f"Edge processing completed in {processing_time:.2f} seconds")
        print(f"Total runtime: {total_time:.2f} seconds")
        
        # Performance metrics
        edges_per_second = processed_edges / processing_time if processing_time > 0 else 0
        print(f"Processing rate: {edges_per_second:.1f} edges/second")
        
        # Print summary
        print("\nClassification Summary:")
        for classification, count in sorted(classification_counts.items()):
            print(f"{classification.capitalize()} edges: {count}")
        print(f"Total: {sum(classification_counts.values())}")
        
        print(f"\nTiming Breakdown:")
        print(f"  Node loading: {load_time:.2f}s")
        print(f"  Entity collection: {collect_time:.2f}s")
        print(f"  Entity normalization: {normalize_time:.2f}s")
        print(f"  Synonym retrieval: {synonyms_time:.2f}s")
        print(f"  Edge processing: {processing_time:.2f}s")
        print(f"  Total: {total_time:.2f}s")
        
        print(f"\nOutput files created:")
        for classification in ['good', 'bad', 'ambiguous']:
            file_path = Path(self.output_dir) / f"{classification}_edges.jsonl"
            print(f"{classification.capitalize()} edges: {file_path}")
    
    def _process_streaming_batch(self, batch_edges: List[Dict[str, Any]], nodes: Dict[str, Any], 
                                normalized_data: Dict[str, Any], synonyms_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Process a batch of edges using the same batched lookup approach.
        
        Args:
            batch_edges: List of edges to process
            nodes: Node data dictionary
            normalized_data: Normalized entity data
            synonyms_data: Synonym data
            
        Returns:
            Dictionary with classification counts for this batch
        """
        # Use existing batched processing logic
        # 1. Collect synonyms from this batch
        synonym_groups = self._collect_synonyms_from_batch(batch_edges, normalized_data, synonyms_data)
        
        # 2. Execute bulk lookups
        lookup_cache = self._execute_bulk_lookups(synonym_groups)
        
        # 3. Process batch with cache and write results
        classification_counts = defaultdict(int)
        
        for edge in batch_edges:
            # Add entity names
            edge['subject_name'] = nodes.get(edge['subject'], {}).get('name', 'Unknown')
            edge['object_name'] = nodes.get(edge['object'], {}).get('name', 'Unknown')
            
            # Classify edge
            classification, debug_info = self.classify_edge(edge, lookup_cache, 
                                                           normalized_data, synonyms_data)
            classification_counts[classification] += 1
            
            # Write result immediately
            self.write_edge_result(edge, classification, debug_info)
        
        return dict(classification_counts)
    
    def _collect_synonyms_from_batch(self, batch_edges: List[Dict[str, Any]], 
                                   normalized_data: Dict[str, Any], synonyms_data: Dict[str, Any]) -> Dict[str, Set[str]]:
        """
        Collect all unique synonyms from a batch, grouped by biolink type (reusing existing logic).
        """
        # Temporarily set edges for existing method to work
        original_edges = self.edges if hasattr(self, 'edges') else []
        original_normalized = self.normalized_data if hasattr(self, 'normalized_data') else {}
        original_synonyms = self.synonyms_data if hasattr(self, 'synonyms_data') else {}
        
        self.edges = batch_edges
        self.normalized_data = normalized_data
        self.synonyms_data = synonyms_data
        
        try:
            result = self.collect_all_synonyms_from_batch(batch_edges)
            return result
        finally:
            # Restore original data
            self.edges = original_edges
            self.normalized_data = original_normalized
            self.synonyms_data = original_synonyms
    
    def _execute_bulk_lookups(self, synonym_groups: Dict[str, Set[str]]) -> Dict[str, List[Dict[str, Any]]]:
        """Execute bulk lookups (reusing existing logic)."""
        return self.execute_bulk_lookups(synonym_groups)
    
    def _create_output_files(self) -> Dict[str, Any]:
        """Create and return output file handles."""
        os.makedirs(self.output_dir, exist_ok=True)
        
        output_files = {}
        for classification in ['good', 'bad', 'ambiguous']:
            file_path = Path(self.output_dir) / f"{classification}_edges.jsonl"
            output_files[classification] = open(file_path, 'w')
        
        return output_files


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 1 edge classification')
    parser.add_argument('--edges', required=True, help='Path to edges JSONL file')
    parser.add_argument('--nodes', required=True, help='Path to nodes JSONL file')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--max-edges', type=int, help='Maximum number of edges to process (for testing)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for streaming processing (default: 1000)')
    
    args = parser.parse_args()
    
    classifier = EdgeClassifier(args.edges, args.nodes, args.output_dir)
    classifier.run_streaming(batch_size=args.batch_size, max_edges=args.max_edges)


if __name__ == '__main__':
    main()