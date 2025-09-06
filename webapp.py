"""
Flask web application for reviewing classified edges.

This webapp allows human reviewers to examine edges that have been classified
by the Phase 1 system as passed, unresolved, or ambiguous entity resolution.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for

from phase1 import CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS, CLASSIFICATION_FILE_MAPPING


class EdgeReviewer:
    """Class to handle loading and managing classified edges."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.edges = {
            CLASSIFICATION_PASSED: [],
            CLASSIFICATION_UNRESOLVED: [],
            CLASSIFICATION_AMBIGUOUS: []
        }
        self.current_indices = {
            CLASSIFICATION_PASSED: 0,
            CLASSIFICATION_UNRESOLVED: 0,
            CLASSIFICATION_AMBIGUOUS: 0
        }
        self.load_all_edges()
    
    
    def load_edges_from_file(self, filename: str) -> List[Dict[str, Any]]:
        """Load edges from a JSONL file."""
        filepath = self.output_dir / filename
        edges = []
        
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            edges.append(json.loads(line))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading {filename}: {e}")
        
        return edges
    
    def load_all_edges(self):
        """Load all classified edges from output files."""
        print("Loading classified edges...")
        
        self.edges[CLASSIFICATION_PASSED] = self.load_edges_from_file(f"{CLASSIFICATION_FILE_MAPPING[CLASSIFICATION_PASSED]}.jsonl")
        self.edges[CLASSIFICATION_UNRESOLVED] = self.load_edges_from_file(f"{CLASSIFICATION_FILE_MAPPING[CLASSIFICATION_UNRESOLVED]}.jsonl")
        self.edges[CLASSIFICATION_AMBIGUOUS] = self.load_edges_from_file(f"{CLASSIFICATION_FILE_MAPPING[CLASSIFICATION_AMBIGUOUS]}.jsonl")
        
        print(f"Loaded edges - {CLASSIFICATION_PASSED}: {len(self.edges[CLASSIFICATION_PASSED])}, "
              f"{CLASSIFICATION_UNRESOLVED}: {len(self.edges[CLASSIFICATION_UNRESOLVED])}, "
              f"{CLASSIFICATION_AMBIGUOUS}: {len(self.edges[CLASSIFICATION_AMBIGUOUS])}")
    
    def get_edge_count(self, classification: str) -> int:
        """Get count of edges for a classification."""
        return len(self.edges.get(classification, []))
    
    def get_edge_by_index(self, classification: str, index: int) -> Optional[Dict[str, Any]]:
        """Get edge by classification and index."""
        edges_list = self.edges.get(classification, [])
        if 0 <= index < len(edges_list):
            return edges_list[index]
        return None
    
    def get_current_edge(self, classification: str) -> Optional[Dict[str, Any]]:
        """Get current edge for a classification."""
        current_idx = self.current_indices.get(classification, 0)
        return self.get_edge_by_index(classification, current_idx)
    
    def set_current_index(self, classification: str, index: int):
        """Set current index for a classification."""
        max_index = len(self.edges.get(classification, [])) - 1
        self.current_indices[classification] = max(0, min(index, max_index))
    
    def next_edge(self, classification: str) -> bool:
        """Move to next edge. Returns True if successful."""
        current_idx = self.current_indices.get(classification, 0)
        max_idx = len(self.edges.get(classification, [])) - 1
        
        if current_idx < max_idx:
            self.current_indices[classification] = current_idx + 1
            return True
        return False
    
    def prev_edge(self, classification: str) -> bool:
        """Move to previous edge. Returns True if successful."""
        current_idx = self.current_indices.get(classification, 0)
        
        if current_idx > 0:
            self.current_indices[classification] = current_idx - 1
            return True
        return False
    
    def get_edge_summary(self) -> Dict[str, int]:
        """Get summary of edge counts."""
        return {
            CLASSIFICATION_PASSED: len(self.edges[CLASSIFICATION_PASSED]),
            CLASSIFICATION_UNRESOLVED: len(self.edges[CLASSIFICATION_UNRESOLVED]),
            CLASSIFICATION_AMBIGUOUS: len(self.edges[CLASSIFICATION_AMBIGUOUS]),
            'total': sum(len(edges) for edges in self.edges.values())
        }


# Create Flask app
app = Flask(__name__)
reviewer = EdgeReviewer("output")


@app.route('/')
def index():
    """Home page showing summary of classified edges."""
    summary = reviewer.get_edge_summary()
    return render_template('index.html', summary=summary)


@app.route('/edges/<classification>')
@app.route('/edges/<classification>/<int:index>')
def view_edges(classification: str, index: int = None):
    """View edges by classification."""
    if classification not in [CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS]:
        return redirect(url_for('index'))
    
    # Set index if provided
    if index is not None:
        reviewer.set_current_index(classification, index)
    
    # Get current edge
    current_edge = reviewer.get_current_edge(classification)
    current_index = reviewer.current_indices[classification]
    total_count = reviewer.get_edge_count(classification)
    
    if current_edge is None and total_count > 0:
        # No current edge but edges exist, go to first one
        reviewer.set_current_index(classification, 0)
        current_edge = reviewer.get_current_edge(classification)
        current_index = 0
    
    return render_template('edge_viewer.html',
                         classification=classification,
                         edge=current_edge,
                         current_index=current_index,
                         total_count=total_count)


@app.route('/api/edges/<classification>/navigate', methods=['POST'])
def navigate_edge(classification: str):
    """API endpoint for edge navigation."""
    if classification not in [CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS]:
        return jsonify({'error': 'Invalid classification'}), 400
    
    action = request.json.get('action')
    
    if action == 'next':
        success = reviewer.next_edge(classification)
    elif action == 'prev':
        success = reviewer.prev_edge(classification)
    elif action == 'goto':
        index = request.json.get('index', 0)
        reviewer.set_current_index(classification, index)
        success = True
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    current_edge = reviewer.get_current_edge(classification)
    current_index = reviewer.current_indices[classification]
    
    return jsonify({
        'success': success,
        'current_index': current_index,
        'edge': current_edge
    })


@app.route('/api/reload')
def reload_edges():
    """API endpoint to reload edges from files."""
    reviewer.load_all_edges()
    return jsonify({'success': True, 'summary': reviewer.get_edge_summary()})


@app.route('/api/lookup/<classification>/<int:index>/<entity_type>/<query>')
def lookup_synonym(classification: str, index: int, entity_type: str, query: str):
    """API endpoint to get stored lookup results for a synonym from edge data."""
    try:
        # Get the specific edge
        edge = reviewer.get_edge_by_index(classification, index)
        if not edge:
            return jsonify({'success': False, 'error': 'Edge not found'}), 404
        
        # Get the lookup data from the edge's debug info
        debug_info = edge.get('qc_debug', {})
        
        if entity_type == 'subject':
            lookup_data = debug_info.get('subject_lookup_data', {})
        elif entity_type == 'object':
            lookup_data = debug_info.get('object_lookup_data', {})
        else:
            return jsonify({'success': False, 'error': 'Invalid entity type'}), 400
        
        # Get ALL results for this entity (combining all synonym variants)
        # This ensures if entity is marked ambiguous, we show ALL matches that caused ambiguity
        all_results = []
        seen_curies = set()
        
        for synonym_results in lookup_data.values():
            for result in synonym_results:
                curie = result['curie']
                if curie not in seen_curies:
                    all_results.append(result)
                    seen_curies.add(curie)
        
        # Sort by score descending
        results = sorted(all_results, key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'success': True, 
            'query': query,
            'entity_type': entity_type,
            'count': len(results),
            'results': results,
            'note': f'Showing all exact matches for {entity_type} entity (clicked synonym: "{query}")'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Template filters for better display
@app.template_filter('format_publications')
def format_publications(publications):
    """Format publication list for display."""
    if not publications:
        return "None"
    
    formatted = []
    for pub in publications:
        if pub.startswith('PMID:'):
            pmid = pub.replace('PMID:', '')
            formatted.append(f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}" target="_blank">{pub}</a>')
        elif pub.startswith('PMC:'):
            pmc = pub.replace('PMC:', '')
            formatted.append(f'<a href="https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}" target="_blank">{pub}</a>')
        else:
            formatted.append(pub)
    
    return ', '.join(formatted)


@app.template_filter('format_sentences')
def format_sentences(sentences):
    """Format sentences for better display."""
    if not sentences or sentences == 'NA':
        return "No supporting sentences available"
    
    # Split on |NA| separator and filter out empty/NA entries
    sentence_list = [s.strip() for s in sentences.split('|NA|') if s.strip() and s.strip() != 'NA']
    
    if not sentence_list:
        return "No supporting sentences available"
    
    # Join sentences with paragraph breaks for better readability
    return '<br><br>'.join(sentence_list)


@app.template_filter('format_curie')
def format_curie(curie):
    """Format CURIE with link if possible."""
    if not curie:
        return curie
    
    # Add links for common prefixes
    if curie.startswith('CHEBI:'):
        chebi_id = curie.replace('CHEBI:', '')
        return f'<a href="https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:{chebi_id}" target="_blank">{curie}</a>'
    elif curie.startswith('UniProtKB:'):
        uniprot_id = curie.replace('UniProtKB:', '')
        return f'<a href="https://www.uniprot.org/uniprot/{uniprot_id}" target="_blank">{curie}</a>'
    elif curie.startswith('HGNC:'):
        hgnc_id = curie.replace('HGNC:', '')
        return f'<a href="https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:{hgnc_id}" target="_blank">{curie}</a>'
    else:
        return curie


@app.template_filter('format_entity_with_name')
def format_entity_with_name(curie, name=None):
    """Format entity with embedded name and CURIE link."""
    if not curie:
        return curie
    
    curie_link = format_curie(curie)
    
    if name and name != curie:
        return f'<strong>{name}</strong><br><small>{curie_link}</small>'
    else:
        return curie_link


@app.template_filter('highlight_synonyms')
def highlight_synonyms(text, edge=None):
    """Highlight found synonyms in text."""
    if not text or not edge:
        return text
    
    # Get debug info if available
    debug_info = edge.get('qc_debug', {})
    subject_synonyms = debug_info.get('subject_synonyms_found', [])
    object_synonyms = debug_info.get('object_synonyms_found', [])
    
    highlighted_text = text
    
    # Highlight subject synonyms in blue
    for synonym in subject_synonyms:
        if synonym:
            # Use case-insensitive word boundary replacement
            pattern = r'\b' + re.escape(synonym) + r'\b'
            highlighted_text = re.sub(
                pattern, 
                f'<span class="synonym-highlight subject-synonym" style="background-color: #cce5ff; padding: 1px 3px; border-radius: 3px; font-weight: bold; cursor: pointer;" title="Subject: {synonym} (click to lookup)">\\g<0></span>',
                highlighted_text,
                flags=re.IGNORECASE
            )
    
    # Highlight object synonyms in red
    for synonym in object_synonyms:
        if synonym:
            # Use case-insensitive word boundary replacement
            pattern = r'\b' + re.escape(synonym) + r'\b'
            highlighted_text = re.sub(
                pattern,
                f'<span class="synonym-highlight object-synonym" style="background-color: #ffcccb; padding: 1px 3px; border-radius: 3px; font-weight: bold; cursor: pointer;" title="Object: {synonym} (click to lookup)">\\g<0></span>',
                highlighted_text,
                flags=re.IGNORECASE
            )
    
    return highlighted_text


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Check if output directory exists
    if not Path('output').exists():
        print("Warning: Output directory doesn't exist. Please run phase1.py first to generate classified edges.")
    
    print("Starting Flask webapp...")
    print("Visit http://localhost:5000 to view the edge reviewer")
    app.run(debug=True, host='0.0.0.0', port=5000)