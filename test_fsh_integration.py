#!/usr/bin/env python3
"""
Integration test for FSH ambiguity detection using real APIs.
This test validates that FSH is correctly classified as ambiguous.
"""

import pytest
from phase1 import EdgeClassifier


def test_fsh_integration():
    """Integration test: FSH should be classified as ambiguous using real APIs."""
    
    # Create test files with our FSH edge
    import tempfile, json, os
    
    edge = {
        'subject': 'GTOPDB:4386',  # FSH receptor 
        'object': 'UniProtKB:P80370',  # Some protein
        'sentences': 'FSH stimulation increased protein X expression.'
    }
    
    nodes = [
        {'id': 'GTOPDB:4386', 'name': 'FSH receptor'},
        {'id': 'UniProtKB:P80370', 'name': 'some protein'}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        edges_file = os.path.join(tmpdir, 'edges.jsonl')
        nodes_file = os.path.join(tmpdir, 'nodes.jsonl')
        
        with open(edges_file, 'w') as f:
            f.write(json.dumps(edge) + '\n')
        
        with open(nodes_file, 'w') as f:
            for node in nodes:
                f.write(json.dumps(node) + '\n')
        
        classifier = EdgeClassifier(edges_file, nodes_file, tmpdir)
        classifier.run_streaming(max_edges=1)
        
        # Check output files for classification result
        output_files = [
            os.path.join(tmpdir, 'ambiguous_edges.jsonl'),
            os.path.join(tmpdir, 'good_edges.jsonl'),
            os.path.join(tmpdir, 'bad_edges.jsonl')
        ]
        
        result = None
        for output_file in output_files:
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, 'r') as f:
                    line = f.readline().strip()
                    if line:
                        data = json.loads(line)
                        result = data.get('qc_classification')
                        break
        
        # FSH should be ambiguous according to our notes and real API behavior
        assert result == 'ambiguous', f"Expected 'ambiguous', got '{result}'"


def test_chebi_fsh_integration():
    """Integration test: CHEBI:81569 with FSH text should be ambiguous."""
    
    # Create test files with our FSH edge
    import tempfile, json, os
    
    edge = {
        'subject': 'CHEBI:81569',  # Follitropin (which has FSH as synonym)
        'object': 'UniProtKB:P80370',  
        'sentences': 'FSH furthermore directly upregulated expression of the protein.'
    }
    
    nodes = [
        {'id': 'CHEBI:81569', 'name': 'follitropin'},
        {'id': 'UniProtKB:P80370', 'name': 'some protein'}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        edges_file = os.path.join(tmpdir, 'edges.jsonl')
        nodes_file = os.path.join(tmpdir, 'nodes.jsonl')
        
        with open(edges_file, 'w') as f:
            f.write(json.dumps(edge) + '\n')
        
        with open(nodes_file, 'w') as f:
            for node in nodes:
                f.write(json.dumps(node) + '\n')
        
        classifier = EdgeClassifier(edges_file, nodes_file, tmpdir)
        classifier.run_streaming(max_edges=1)
        
        # Check output files for classification result
        output_files = [
            os.path.join(tmpdir, 'ambiguous_edges.jsonl'),
            os.path.join(tmpdir, 'good_edges.jsonl'),
            os.path.join(tmpdir, 'bad_edges.jsonl')
        ]
        
        result = None
        for output_file in output_files:
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, 'r') as f:
                    line = f.readline().strip()
                    if line:
                        data = json.loads(line)
                        result = data.get('qc_classification')
                        break
        
        # Should be ambiguous since FSH maps to multiple entities
        assert result == 'ambiguous', f"Expected 'ambiguous', got '{result}'"


if __name__ == '__main__':
    # Can run as standalone script for debugging
    print("Running FSH integration tests...")
    test_fsh_integration()
    test_chebi_fsh_integration()
    print("All integration tests passed!")
