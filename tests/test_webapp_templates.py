"""
Tests for webapp templates that would have caught the jinja2 template error.

This test verifies that webapp templates can be rendered with the expected
data structure from the webapp, catching template/data mismatches.
"""

import pytest
from jinja2 import Environment, FileSystemLoader, UndefinedError
from pathlib import Path

from phase1 import CLASSIFICATION_PASSED, CLASSIFICATION_UNRESOLVED, CLASSIFICATION_AMBIGUOUS
from webapp import EdgeReviewer


class TestWebappTemplates:
    """Test webapp templates for compatibility with classification constants."""
    
    def setup_method(self):
        """Set up jinja2 environment and test data."""
        # Set up Jinja2 environment pointing to templates directory
        templates_dir = Path(__file__).parent.parent / 'templates'
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            undefined=pytest.importorskip("jinja2").StrictUndefined  # Make undefined variables raise errors
        )
        
        # Add Flask-like globals that templates expect
        def mock_url_for(endpoint, **values):
            return f"/{endpoint}"
        
        def mock_format_entity_with_name(entity_id, entity_name=None):
            return f"{entity_id} ({entity_name or 'Unknown'})"
        
        def mock_format_sentences(sentences):
            return sentences
            
        def mock_highlight_synonyms(sentences, edge):
            return sentences
            
        def mock_format_publications(publications):
            return publications if publications else ""
        
        self.jinja_env.globals['url_for'] = mock_url_for
        self.jinja_env.filters['format_entity_with_name'] = mock_format_entity_with_name
        self.jinja_env.filters['format_sentences'] = mock_format_sentences
        self.jinja_env.filters['highlight_synonyms'] = mock_highlight_synonyms
        self.jinja_env.filters['format_publications'] = mock_format_publications
        
        # Mock summary data structure that webapp.py produces
        self.mock_summary = {
            CLASSIFICATION_PASSED: 15,
            CLASSIFICATION_UNRESOLVED: 42, 
            CLASSIFICATION_AMBIGUOUS: 8,
            'total': 65
        }
        
        # Also test the old data structure that would break after refactoring
        self.old_summary = {
            'good': 15,
            'bad': 42,
            'ambiguous': 8, 
            'total': 65
        }

    def test_index_template_renders_with_new_constants(self):
        """
        Critical test that would have caught the jinja2.exceptions.UndefinedError.
        
        This verifies the index template can render with the new classification constants.
        """
        template = self.jinja_env.get_template('index.html')
        
        # This should render successfully with new constants
        try:
            rendered = template.render(summary=self.mock_summary)
            assert rendered, "Template should render non-empty content"
            
            # Verify the new classification names appear in rendered output
            assert CLASSIFICATION_PASSED in rendered or "Passed Phase 1" in rendered
            assert CLASSIFICATION_UNRESOLVED in rendered or "Unresolved Entity" in rendered  
            assert CLASSIFICATION_AMBIGUOUS in rendered or "Ambiguous Entity Resolution" in rendered
            
            # Verify the counts appear in rendered output
            assert "15" in rendered  # passed count
            assert "42" in rendered  # unresolved count
            assert "8" in rendered   # ambiguous count
            assert "65" in rendered  # total count
            
            print("✅ Template renders successfully with new constants")
            
        except UndefinedError as e:
            pytest.fail(f"Template failed to render with new constants due to UndefinedError: {e}")
        except Exception as e:
            pytest.fail(f"Template failed to render with new constants: {e}")

    def test_index_template_fails_with_old_data_structure(self):
        """
        Test that demonstrates the template would fail with old data structure.
        
        This shows that our test would have caught the incompatibility.
        """
        template = self.jinja_env.get_template('index.html')
        
        # This should fail with old data structure after refactoring
        with pytest.raises((UndefinedError, KeyError)):
            template.render(summary=self.old_summary)
        
        print("✅ Template correctly fails with old data structure (as expected)")

    def test_all_templates_can_be_loaded(self):
        """Test that all template files can be loaded without syntax errors."""
        templates_dir = Path(__file__).parent.parent / 'templates'
        
        for template_file in templates_dir.glob('*.html'):
            try:
                template = self.jinja_env.get_template(template_file.name)
                # Try to identify required variables by attempting render with empty context
                # This will show us what variables the template expects
                print(f"✅ Template {template_file.name} loaded successfully")
            except Exception as e:
                pytest.fail(f"Failed to load template {template_file.name}: {e}")

    def test_webapp_produces_expected_summary_structure(self):
        """
        Test that webapp EdgeReviewer produces the expected summary structure.
        
        This ensures the data structure matches what templates expect.
        """
        # Mock an EdgeReviewer (this would normally load from files)
        reviewer = EdgeReviewer("nonexistent")  # Will create empty data
        
        # Override with test data
        reviewer.edges = {
            CLASSIFICATION_PASSED: [{"test": "edge1"}] * 10,
            CLASSIFICATION_UNRESOLVED: [{"test": "edge2"}] * 25,
            CLASSIFICATION_AMBIGUOUS: [{"test": "edge3"}] * 5,
        }
        
        summary = reviewer.get_edge_summary()
        
        # Verify structure matches what templates expect
        assert isinstance(summary, dict)
        assert CLASSIFICATION_PASSED in summary
        assert CLASSIFICATION_UNRESOLVED in summary
        assert CLASSIFICATION_AMBIGUOUS in summary
        assert 'total' in summary
        
        # Verify counts are correct
        assert summary[CLASSIFICATION_PASSED] == 10
        assert summary[CLASSIFICATION_UNRESOLVED] == 25
        assert summary[CLASSIFICATION_AMBIGUOUS] == 5
        assert summary['total'] == 40
        
        print(f"✅ Webapp produces expected summary structure: {summary}")

    def test_template_constants_match_phase1_constants(self):
        """
        Test that ensures templates are updated when phase1 constants change.
        
        This test will fail if someone changes the phase1 constants but forgets
        to update the templates.
        """
        template_path = Path(__file__).parent.parent / 'templates' / 'index.html'
        template_content = template_path.read_text()
        
        # Check that template references the correct constant values
        # (This is a basic check - in practice you'd want more sophisticated parsing)
        
        # The template should reference the new classification names
        expected_references = [
            "passed phase 1",  # Should appear in template
            "unresolved entity", 
            "ambiguous entity resolution"
        ]
        
        for expected_ref in expected_references:
            assert expected_ref in template_content.lower(), \
                f"Template should reference '{expected_ref}' but doesn't. " \
                f"Template may need updating after classification constant changes."
        
        # The template should NOT reference old classification names
        old_references = ["summary.good", "summary.bad", "summary.ambiguous"]
        
        for old_ref in old_references:
            assert old_ref not in template_content, \
                f"Template still contains old reference '{old_ref}'. " \
                f"Template needs updating for new classification constants."
        
        print("✅ Template constants match phase1 constants")

    def test_edge_viewer_template_compatibility(self):
        """Test that edge_viewer template works with classification constants."""
        template = self.jinja_env.get_template('edge_viewer.html')
        
        # Mock data for edge viewer
        mock_edge = {
            "subject": "CHEBI:123", 
            "object": "HGNC:456",
            "qc_classification": CLASSIFICATION_PASSED,
            "sentences": "Test sentence",
            "subject_name": "Test Chemical",
            "object_name": "Test Gene",
            "predicate": "biolink:affects",
            "publications": "PMID:12345",
            "primary_knowledge_source": "test_source",
            "agent_type": "test_agent"
        }
        
        mock_context = {
            'classification': CLASSIFICATION_PASSED,
            'edge': mock_edge,
            'current_index': 0,
            'total_count': 1
        }
        
        try:
            rendered = template.render(**mock_context)
            assert rendered, "Edge viewer template should render"
            assert CLASSIFICATION_PASSED in rendered
            print("✅ Edge viewer template compatible with classification constants")
            
        except UndefinedError as e:
            pytest.fail(f"Edge viewer template failed due to UndefinedError: {e}")