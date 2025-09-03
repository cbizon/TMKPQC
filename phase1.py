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
        
        # Data storage
        self.edges = []
        self.nodes = {}
        self.normalized_entities = {}
        self.synonyms_data = {}
        
        # Output files
        self.good_edges_file = self.output_dir / "good_edges.jsonl"
        self.bad_edges_file = self.output_dir / "bad_edges.jsonl" 
        self.ambiguous_edges_file = self.output_dir / "ambiguous_edges.jsonl"
        
        # Clear existing output files
        for output_file in [self.good_edges_file, self.bad_edges_file, self.ambiguous_edges_file]:
            if output_file.exists():
                output_file.unlink()
    
    def load_data(self, max_edges: int = None) -> None:
        """
        Load edges and nodes from JSONL files.
        
        Args:
            max_edges: Maximum number of edges to load (for testing). If None, load all.
        """
        print("Loading nodes...")
        with open(self.nodes_file, 'r') as f:
            for line in f:
                node = json.loads(line.strip())
                self.nodes[node['id']] = node
        
        print(f"Loaded {len(self.nodes)} nodes")
        
        print("Loading edges...")
        with open(self.edges_file, 'r') as f:
            for i, line in enumerate(f):
                if max_edges and i >= max_edges:
                    break
                edge = json.loads(line.strip())
                edge['edge_id'] = str(uuid.uuid4())  # Add unique ID for tracking
                self.edges.append(edge)
        
        print(f"Loaded {len(self.edges)} edges")
    
    def collect_entities(self) -> Set[str]:
        """
        Collect all unique entities (subjects and objects) from edges.
        
        Returns:
            Set of all unique CURIEs
        """
        entities = set()
        for edge in self.edges:
            entities.add(edge['subject'])
            entities.add(edge['object'])
        
        print(f"Found {len(entities)} unique entities")
        return entities
    
    def normalize_entities(self, entities: Set[str]) -> None:
        """
        Normalize entities using the node normalizer API.
        
        Args:
            entities: Set of CURIEs to normalize
        """
        print("Normalizing entities...")
        entities_list = list(entities)
        
        try:
            self.normalized_entities = batch_get_normalized_nodes(entities_list)
        except APIException as e:
            print(f"Error normalizing entities: {e}")
            raise
        
        print(f"Normalized {len(self.normalized_entities)} entities")
    
    def get_all_synonyms(self) -> None:
        """Get synonyms for all preferred identifiers."""
        print("Getting synonyms...")
        
        # Extract preferred identifiers from normalized entities
        preferred_curies = []
        for curie, data in self.normalized_entities.items():
            if data and 'id' in data and 'identifier' in data['id']:
                preferred_curies.append(data['id']['identifier'])
        
        # Remove duplicates
        preferred_curies = list(set(preferred_curies))
        
        try:
            self.synonyms_data = batch_get_synonyms(preferred_curies)
        except APIException as e:
            print(f"Error getting synonyms: {e}")
            raise
        
        print(f"Got synonyms for {len(self.synonyms_data)} entities")
    
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
    
    def check_ambiguous_matches(self, found_synonyms: List[str], expected_biolink_type: str = None) -> Tuple[bool, Dict[str, List[Dict]]]:
        """
        Check if found synonyms are ambiguous by looking them up with enhanced preferred name logic.
        
        Enhanced Logic:
        - If a synonym has multiple exact matches, check if any match has that synonym as preferred name
        - If exactly one match has the synonym as preferred name, prefer that match (not ambiguous)
        - If zero or multiple matches have the synonym as preferred name, remain ambiguous
        
        Args:
            found_synonyms: List of synonyms found in text
            expected_biolink_type: Expected biolink type to filter results
        
        Returns:
            Tuple of (is_ambiguous, lookup_data) where lookup_data maps synonyms to their exact matches
        """
        is_ambiguous = False
        lookup_data = {}
        
        for synonym in found_synonyms:
            try:
                # For genes, filter by human taxon to avoid multi-species confusion
                only_taxa = None
                if expected_biolink_type and 'gene' in expected_biolink_type.lower():
                    only_taxa = ["NCBITaxon:9606"]
                
                lookup_results = lookup_names(
                    query=synonym,
                    limit=20,
                    biolink_type=expected_biolink_type,
                    only_taxa=only_taxa
                )
                
                # Find results that have this exact synonym as a separate element in the list
                exact_matches = []
                for result in lookup_results:
                    result_synonyms = result.get('synonyms', [])
                    # Check for exact string match in the synonyms list (not substring)
                    if synonym in result_synonyms:
                        exact_matches.append(self._format_lookup_result(result))
                
                # Store the exact matches for this synonym
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
                    
            except APIException as e:
                print(f"Warning: Could not lookup synonym '{synonym}': {e}")
                lookup_data[synonym] = []
                continue
        
        return is_ambiguous, lookup_data
    
    def classify_edge(self, edge: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Classify a single edge as 'good', 'bad', or 'ambiguous'.
        
        Args:
            edge: Edge dictionary
        
        Returns:
            Tuple of (classification string, debug info dictionary)
        """
        subject_id = edge['subject']
        object_id = edge['object']
        sentences = edge.get('sentences', '')
        
        # Initialize debug info
        debug_info = {
            'subject_synonyms_found': [],
            'object_synonyms_found': [],
            'subject_all_synonyms': [],
            'object_all_synonyms': []
        }
        
        if not sentences or sentences == 'NA':
            return 'bad', debug_info  # No text to validate against
        
        # Get normalized data for subject and object
        subject_norm = self.normalized_entities.get(subject_id)
        object_norm = self.normalized_entities.get(object_id)
        
        if not subject_norm or not object_norm:
            return 'bad', debug_info  # Could not normalize entities
        
        # Get preferred identifiers
        subject_preferred = subject_norm.get('id', {}).get('identifier') if subject_norm else None
        object_preferred = object_norm.get('id', {}).get('identifier') if object_norm else None
        
        if not subject_preferred or not object_preferred:
            return 'bad', debug_info  # No preferred identifiers
        
        # Get synonyms
        subject_synonyms_data = self.synonyms_data.get(subject_preferred, {})
        object_synonyms_data = self.synonyms_data.get(object_preferred, {})
        
        subject_synonyms = subject_synonyms_data.get('names', []) if subject_synonyms_data else []
        object_synonyms = object_synonyms_data.get('names', []) if object_synonyms_data else []
        
        # Store all synonyms in debug info
        debug_info['subject_all_synonyms'] = subject_synonyms.copy()
        debug_info['object_all_synonyms'] = object_synonyms.copy()
        
        # Find synonyms in text
        subject_found = self.find_synonyms_in_text(sentences, subject_synonyms)
        object_found = self.find_synonyms_in_text(sentences, object_synonyms)
        
        # Store found synonyms in debug info
        debug_info['subject_synonyms_found'] = subject_found.copy()
        debug_info['object_synonyms_found'] = object_found.copy()
        
        # Check if entities are mentioned in text
        if not subject_found and not object_found:
            return 'bad', debug_info  # Neither entity mentioned
        elif not subject_found or not object_found:
            return 'bad', debug_info  # Only one entity mentioned
        
        # Check for ambiguity
        subject_types = subject_norm.get('type', []) if subject_norm else []
        object_types = object_norm.get('type', []) if object_norm else []
        
        subject_biolink_type = subject_types[0].replace('biolink:', '') if subject_types else None
        object_biolink_type = object_types[0].replace('biolink:', '') if object_types else None
        
        subject_ambiguous, subject_lookup_data = self.check_ambiguous_matches(subject_found, subject_biolink_type)
        object_ambiguous, object_lookup_data = self.check_ambiguous_matches(object_found, object_biolink_type)
        
        # Add ambiguity flags and lookup data to debug info for webapp display
        debug_info['subject_ambiguous'] = subject_ambiguous
        debug_info['object_ambiguous'] = object_ambiguous
        debug_info['subject_lookup_data'] = subject_lookup_data
        debug_info['object_lookup_data'] = object_lookup_data
        
        if subject_ambiguous or object_ambiguous:
            return 'ambiguous', debug_info
        
        return 'good', debug_info
    
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
    
    def process_batch_with_cache(self, edges: List[Dict[str, Any]], 
                                lookup_cache: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """
        Process a batch of edges using cached lookup results.
        
        Args:
            edges: List of edges to process
            lookup_cache: Cached lookup results for synonyms
            
        Returns:
            Dictionary with classification counts for this batch
        """
        classification_counts = defaultdict(int)
        
        for edge in edges:
            classification, debug_info = self.classify_edge_with_cache(edge, lookup_cache)
            classification_counts[classification] += 1
            self.write_edge_result(edge, classification, debug_info)
        
        return dict(classification_counts)
    
    def classify_edge_with_cache(self, edge: Dict[str, Any], 
                                lookup_cache: Dict[str, List[Dict[str, Any]]]) -> Tuple[str, Dict[str, Any]]:
        """
        Classify an edge using cached lookup results instead of making API calls.
        
        Args:
            edge: Edge to classify
            lookup_cache: Cached lookup results
            
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
            
        # Get entity synonyms
        subject_synonyms = self.synonyms_data.get(edge.get('subject'), [])
        object_synonyms = self.synonyms_data.get(edge.get('object'), [])
        
        if not subject_synonyms or not object_synonyms:
            debug_info['reason'] = 'Missing synonyms for subject or object'
            return 'bad', debug_info
        
        # Check subject and object using cached lookups
        subject_found = self._check_entity_in_text_with_cache(
            edge.get('sentences'), subject_synonyms, lookup_cache, debug_info, 'subject')
        object_found = self._check_entity_in_text_with_cache(
            edge.get('sentences'), object_synonyms, lookup_cache, debug_info, 'object')
        
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
        """
        found_synonyms = self.find_synonyms_in_text(text, synonyms)
        if not found_synonyms:
            return False
        
        # Use the enhanced ambiguity logic with cached results
        is_ambiguous, filtered_lookup_data = self.check_ambiguous_matches_with_cache(found_synonyms, lookup_cache)
        
        # Store debug information
        debug_info[f'{entity_type}_synonyms_found'] = found_synonyms
        debug_info[f'{entity_type}_ambiguous'] = is_ambiguous
        
        return not is_ambiguous
    
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
    
    def process_all_edges_batched(self, batch_size: int = 1000) -> Dict[str, int]:
        """
        Process all edges using outer batching approach with bulk lookups.
        
        Args:
            batch_size: Number of edges to process in each batch
            
        Returns:
            Dictionary with classification counts
        """
        print(f"Processing edges in batches of {batch_size}...")
        total_classification_counts = defaultdict(int)
        total_edges = len(self.edges)
        
        for i in range(0, total_edges, batch_size):
            batch_end = min(i + batch_size, total_edges)
            batch = self.edges[i:batch_end]
            batch_num = i // batch_size + 1
            total_batches = (total_edges + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} edges)")
            
            # Step 1: Collect all synonyms from this batch
            start_time = time.time()
            synonym_groups = self.collect_all_synonyms_from_batch(batch)
            collect_time = time.time() - start_time
            
            # Step 2: Execute bulk lookups for all synonym groups
            start_time = time.time()
            lookup_cache = self.execute_bulk_lookups(synonym_groups)
            lookup_time = time.time() - start_time
            
            # Step 3: Process all edges in batch with cached results
            start_time = time.time()
            batch_counts = self.process_batch_with_cache(batch, lookup_cache)
            process_time = time.time() - start_time
            
            # Update total counts
            for classification, count in batch_counts.items():
                total_classification_counts[classification] += count
            
            print(f"  Batch {batch_num} completed: collect={collect_time:.2f}s, lookup={lookup_time:.2f}s, process={process_time:.2f}s")
        
        print(f"Completed processing {total_edges} edges")
        return dict(total_classification_counts)

    def process_all_edges(self) -> Dict[str, int]:
        """
        Process all edges and classify them (legacy method for compatibility).
        
        Returns:
            Dictionary with classification counts
        """
        print("Processing edges...")
        classification_counts = defaultdict(int)
        
        for i, edge in enumerate(self.edges):
            if i % 1000 == 0:
                print(f"Processed {i}/{len(self.edges)} edges")
            
            classification, debug_info = self.classify_edge(edge)
            classification_counts[classification] += 1
            
            self.write_edge_result(edge, classification, debug_info)
        
        print(f"Completed processing {len(self.edges)} edges")
        return dict(classification_counts)
    
    def run(self, max_edges: int = None) -> None:
        """
        Run the complete Phase 1 classification process with detailed timing.
        
        Args:
            max_edges: Maximum number of edges to process (for testing)
        """
        overall_start_time = time.time()
        print("Starting Phase 1 edge classification...")
        
        # Load data
        start_time = time.time()
        self.load_data(max_edges)
        load_time = time.time() - start_time
        print(f"Data loading completed in {load_time:.2f} seconds")
        
        # Collect and normalize entities
        start_time = time.time()
        entities = self.collect_entities()
        collect_time = time.time() - start_time
        
        start_time = time.time()
        self.normalize_entities(entities)
        normalize_time = time.time() - start_time
        print(f"Entity normalization completed in {normalize_time:.2f} seconds")
        
        # Get synonyms
        start_time = time.time()
        self.get_all_synonyms()
        synonyms_time = time.time() - start_time
        print(f"Synonym retrieval completed in {synonyms_time:.2f} seconds")
        
        # Process all edges using batched approach
        start_time = time.time()
        results = self.process_all_edges_batched()
        processing_time = time.time() - start_time
        total_time = time.time() - overall_start_time
        
        print(f"Edge processing completed in {processing_time:.2f} seconds")
        print(f"Total runtime: {total_time:.2f} seconds")
        
        # Performance metrics
        edges_per_second = len(self.edges) / processing_time if processing_time > 0 else 0
        print(f"Processing rate: {edges_per_second:.1f} edges/second")
        
        # Print summary
        print("\nClassification Summary:")
        print(f"Good edges: {results.get('good', 0)}")
        print(f"Bad edges: {results.get('bad', 0)}")
        print(f"Ambiguous edges: {results.get('ambiguous', 0)}")
        print(f"Total: {sum(results.values())}")
        
        print(f"\nTiming Breakdown:")
        print(f"  Data loading: {load_time:.2f}s")
        print(f"  Entity collection: {collect_time:.2f}s") 
        print(f"  Entity normalization: {normalize_time:.2f}s")
        print(f"  Synonym retrieval: {synonyms_time:.2f}s")
        print(f"  Edge processing: {processing_time:.2f}s")
        print(f"  Total: {total_time:.2f}s")
        
        # Estimate full dataset time if this is a sample
        if max_edges:
            # Get total edge count
            total_edges = 0
            with open(self.edges_file, 'r') as f:
                for line in f:
                    total_edges += 1
            
            if total_edges > len(self.edges):
                # Estimate based on processing rate (excluding one-time setup costs)
                setup_time = load_time + normalize_time + synonyms_time
                per_edge_time = processing_time / len(self.edges)
                estimated_processing_time = total_edges * per_edge_time
                estimated_total_time = setup_time + estimated_processing_time
                
                print(f"\nFull Dataset Estimation:")
                print(f"  Total edges in dataset: {total_edges:,}")
                print(f"  Setup time (one-time): {setup_time:.2f}s")
                print(f"  Estimated processing time: {estimated_processing_time/60:.1f} minutes")
                print(f"  Estimated total time: {estimated_total_time/60:.1f} minutes ({estimated_total_time/3600:.1f} hours)")
        
        print(f"\nOutput files created:")
        print(f"Good edges: {self.good_edges_file}")
        print(f"Bad edges: {self.bad_edges_file}")
        print(f"Ambiguous edges: {self.ambiguous_edges_file}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 1 edge classification')
    parser.add_argument('--edges', required=True, help='Path to edges JSONL file')
    parser.add_argument('--nodes', required=True, help='Path to nodes JSONL file')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--max-edges', type=int, help='Maximum number of edges to process (for testing)')
    
    args = parser.parse_args()
    
    classifier = EdgeClassifier(args.edges, args.nodes, args.output_dir)
    classifier.run(args.max_edges)


if __name__ == '__main__':
    main()