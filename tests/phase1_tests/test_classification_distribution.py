"""
High-level tests to ensure classification distribution is reasonable.

These tests act as "smoke tests" to catch major regressions where
the classification system breaks and produces unrealistic distributions.
"""

import json
import tempfile
import subprocess
from pathlib import Path
import pytest

from phase1 import CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS


class TestClassificationDistribution:
    """High-level tests to ensure classification produces reasonable distributions."""

    def test_small_sample_produces_mixed_classifications(self):
        """
        Smoke test: Run on small sample and ensure we get some variety.
        
        This would have caught the bug where everything was classified as unresolved.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run classification on small sample 
            result = subprocess.run([
                'python', 'phase1.py', 
                'tmkp_edges.jsonl', 'tmkp_nodes.jsonl',
                '--output', temp_dir,
                '--max-edges', '50'
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            # Should complete successfully
            assert result.returncode == 0, f"phase1.py failed: {result.stderr}"
            
            # Read results
            classification_counts = {}
            total_processed = 0
            
            for classification in [CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS]:
                file_path = Path(temp_dir) / f"{classification.replace(' ', '_')}.jsonl"
                count = 0
                
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        for line in f:
                            if line.strip():
                                count += 1
                                total_processed += 1
                
                classification_counts[classification] = count
            
            # Verify we processed edges
            assert total_processed > 0, "Should have processed at least some edges"
            assert total_processed <= 50, f"Should not process more than 50 edges, got {total_processed}"
            
            # CRITICAL: Should not have ALL edges as unresolved (this would catch the bug)
            unresolved_percentage = classification_counts[CLASSIFICATION_UNRESOLVED] / total_processed if total_processed > 0 else 0
            assert unresolved_percentage < 0.95, \
                f"Too many edges classified as unresolved ({unresolved_percentage:.1%}). " \
                f"This suggests a systematic bug in classification logic. " \
                f"Distribution: {classification_counts}"
            
            # Should have at least some variety (not all one type)
            non_zero_classifications = sum(1 for count in classification_counts.values() if count > 0)
            assert non_zero_classifications >= 2, \
                f"Should have at least 2 different classification types, got {non_zero_classifications}. " \
                f"Distribution: {classification_counts}"
            
            print(f"✅ Reasonable distribution: {classification_counts} ({total_processed} total)")

    def test_classification_files_created_with_correct_names(self):
        """
        Test that classification files are created with expected names.
        
        This ensures CLASSIFICATION_FILE_MAPPING works correctly.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run classification on small sample
            result = subprocess.run([
                'python', 'phase1.py',
                'tmkp_edges.jsonl', 'tmkp_nodes.jsonl', 
                '--output', temp_dir,
                '--max-edges', '10'
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            assert result.returncode == 0, f"phase1.py failed: {result.stderr}"
            
            # Check that files are created with expected names
            expected_files = [
                "passed_phase_1.jsonl",
                "unresolved_entity.jsonl", 
                "ambiguous_entity_resolution.jsonl"
            ]
            
            for expected_file in expected_files:
                file_path = Path(temp_dir) / expected_file
                assert file_path.exists(), f"Expected output file {expected_file} was not created"
                
                # File should be readable JSON lines
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            if line.strip():
                                edge = json.loads(line)
                                assert 'qc_classification' in edge, \
                                    f"Edge in {expected_file} missing qc_classification field"
                except json.JSONDecodeError as e:
                    pytest.fail(f"File {expected_file} contains invalid JSON: {e}")
            
            print(f"✅ All expected output files created with correct names")

    def test_classification_output_contains_required_fields(self):
        """
        Test that classified edges contain all required fields.
        
        This ensures the classification process adds proper metadata.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run classification
            result = subprocess.run([
                'python', 'phase1.py',
                'tmkp_edges.jsonl', 'tmkp_nodes.jsonl',
                '--output', temp_dir, 
                '--max-edges', '5'
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            assert result.returncode == 0, f"phase1.py failed: {result.stderr}"
            
            # Check all output files for required fields
            required_fields = [
                'qc_classification',
                'qc_phase', 
                'qc_debug',
                'edge_id'
            ]
            
            edges_found = False
            
            for classification_file in Path(temp_dir).glob('*.jsonl'):
                with open(classification_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        if line.strip():
                            edges_found = True
                            try:
                                edge = json.loads(line)
                                
                                for field in required_fields:
                                    assert field in edge, \
                                        f"Missing required field '{field}' in {classification_file.name} line {line_num}"
                                
                                # Verify qc_classification is valid
                                qc_classification = edge['qc_classification']
                                assert qc_classification in [CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS], \
                                    f"Invalid qc_classification '{qc_classification}' in {classification_file.name} line {line_num}"
                                
                            except json.JSONDecodeError as e:
                                pytest.fail(f"Invalid JSON in {classification_file.name} line {line_num}: {e}")
            
            assert edges_found, "Should have found at least one classified edge"
            print("✅ All classified edges contain required fields")

    @pytest.mark.slow
    def test_larger_sample_maintains_reasonable_distribution(self):
        """
        Slower test with larger sample to verify distribution stability.
        
        This catches issues that only appear with larger datasets.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run on larger sample
            result = subprocess.run([
                'python', 'phase1.py',
                'tmkp_edges.jsonl', 'tmkp_nodes.jsonl',
                '--output', temp_dir,
                '--max-edges', '200'
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            assert result.returncode == 0, f"phase1.py failed: {result.stderr}"
            
            # Analyze distribution
            classification_counts = {}
            total_processed = 0
            
            for classification in [CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS]:
                file_path = Path(temp_dir) / f"{classification.replace(' ', '_')}.jsonl"
                count = 0
                
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        for line in f:
                            if line.strip():
                                count += 1
                
                classification_counts[classification] = count
                total_processed += count
            
            # Verify reasonable distribution for larger sample
            if total_processed > 0:
                unresolved_pct = classification_counts[CLASSIFICATION_UNRESOLVED] / total_processed
                passed_pct = classification_counts[CLASSIFICATION_PASSED] / total_processed
                ambiguous_pct = classification_counts[CLASSIFICATION_AMBIGUOUS] / total_processed
                
                # With larger samples, we expect some passed edges
                assert passed_pct > 0.05 or total_processed < 50, \
                    f"With {total_processed} edges, expected >5% passed, got {passed_pct:.1%}. " \
                    f"Distribution: {classification_counts}"
                
                # Should not be overwhelmingly unresolved
                assert unresolved_pct < 0.9, \
                    f"Too many edges unresolved ({unresolved_pct:.1%}) suggests systematic issue. " \
                    f"Distribution: {classification_counts}"
                
                # Should have some variety
                non_zero_types = sum(1 for count in classification_counts.values() if count > 0)
                assert non_zero_types >= 2, \
                    f"Expected variety in classifications, got only {non_zero_types} types. " \
                    f"Distribution: {classification_counts}"
            
            print(f"✅ Larger sample reasonable distribution: {classification_counts}")

    def test_performance_benchmark(self):
        """
        Basic performance test to catch major performance regressions.
        
        This ensures the classification system runs in reasonable time.
        """
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()
            
            result = subprocess.run([
                'python', 'phase1.py',
                'tmkp_edges.jsonl', 'tmkp_nodes.jsonl', 
                '--output', temp_dir,
                '--max-edges', '100'
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert result.returncode == 0, f"phase1.py failed: {result.stderr}"
            
            # Should complete in reasonable time (generous bound to avoid flakiness)
            assert duration < 300, f"Classification took too long: {duration:.1f}s for 100 edges"
            
            # Calculate rough throughput
            throughput = 100 / duration if duration > 0 else float('inf')
            print(f"✅ Performance: 100 edges in {duration:.1f}s ({throughput:.1f} edges/sec)")
            
            # Warn if very slow (but don't fail - might be system dependent)
            if throughput < 0.5:
                print(f"⚠️  Warning: Low throughput {throughput:.2f} edges/sec - potential performance issue")