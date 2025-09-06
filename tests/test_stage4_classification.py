#!/usr/bin/env python3
"""
Test Stage 4: Classification Logic with exact expected input/output.
"""

import pytest
from phase1 import stage4_classification_logic


def test_stage4_fsh_edge_classification():
    """Test Stage 4 classification for FSH edge - should be AMBIGUOUS due to multiple FSH matches."""
    
    # Real edge with FSH and DLK1 entities (exact from pipeline)
    edge = {
        'subject': 'CHEBI:81569',
        'predicate': 'biolink:affects', 
        'object': 'UniProtKB:P80370',
        'primary_knowledge_source': 'infores:text-mining-provider-targeted',
        'publications': ['PMC:9308958', 'PMC:9308958', 'PMC:9308958'],
        'biolink:tmkp_confidence_score': 0.9913376566666666,
        'sentences': 'In our invitro approach FSH furthermore directly upregulated expression of the non-canonical Notch ligand DLK1 establishing a link between FSH/FSHR and DLK1 that, to our knowledge, has not been reported previously.|NA|(D) FSH stimulation for 8?h on Day 8 of differentiation reduced FSHR expression and increased expression of Inhibin ? subunit (INHA), Steroidogenic Acute Regulatory Protein (StAR) and Delta Like Non-Canonical Notch Ligand (DLK1) in WT cells (black bars) but not in A189V mutant lines (light and dark gray bars).|NA|The expression of steroidogenic acute regulatory protein (StAR) and delta like non-canonical notch ligand 1 (DLK1) were also stimulated by FSH and forskolin (Fig.?1D) [FSH stimulations ANOVA, Bonferroni test, P (StAR, FSH 10?ng/ml) = 0.068, P (StAR, FSH 100?ng/ml) = 4.6E?05, P (DLK1, FSH 10?ng/ml) = 0.754, P (DLK1, FSH 100?ng/ml) = 0.002, forskolin t-test, adjusted P (StAR) = 1.34E?08,|NA',
        'tmkp_ids': ['tmkp:91b3c883a4bfff31749e96cf07c54b645c8970e00b1e0d51375f3507326bd3b2', 'tmkp:f412ff05026d6c987d53c91ff00142a953eaaea2206e691ddbb8840652675631', 'tmkp:e830a6e9dd99c46741c73a3c5e65150e000385d3d2491851354aea613a213a82'],
        'knowledge_level': 'not_provided',
        'agent_type': 'text_mining_agent',
        'qualified_predicate': 'biolink:causes',
        'object_aspect_qualifier': 'activity_or_abundance',
        'object_direction_qualifier': 'increased'
    }
    
    # Real lookup cache from Stage 3 (exact results from pipeline)
    lookup_cache = {
        'DLK1': [{
            'curie': 'NCBIGene:8788', 'label': 'DLK1', 'highlighting': {},
            'synonyms': ['DLK', 'pG2', 'ZOG', 'FA1', 'DLK1', 'PREF1', 'DLK-1', 'Delta1', 'Pref-1', 'DLK1 Gene', 'DLK1 gene', 'secredeltin', 'FETAL ANTIGEN 1', 'fetal antigen 1', 'delta-like 1 homolog', 'PREADIPOCYTE FACTOR 1', 'preadipocyte factor 1', 'protein delta homolog 1', 'delta-like homolog (Drosophila)', 'delta-like 1 homolog (Drosophila)', 'DELTA, DROSOPHILA, HOMOLOG-LIKE 1', 'DELTA-LIKE NONCANONICAL NOTCH LIGAND 1', 'Delta-Like 1 Homolog (Drosophila) Gene', 'delta like non-canonical Notch ligand 1', 'FA1 protein, human', 'DLK1 protein, human', 'Dll1 protein, human', 'PREF1 protein, human', 'Pref-1 protein, human', 'hDLK1-A protein, human', 'fetal antigen-1, human', 'fetal antigen 1, human', 'secredeltin protein, human', 'delta-like 1 protein, human', 'preadipocyte factor 1, human', 'pre-adipocyte factor 1, human', 'A8K019_HUMAN Protein delta homolog 1 (trembl)', 'delta-like 1 homolog (Drosophila) protein, human', 'hDLK1', 'pG2 (human)', 'DLK-1 (human)', 'Protein Delta Homolog 1', 'protein delta homolog 1 (human)', 'DLK1_HUMAN Protein delta homolog 1 (sprot)'],
            'taxa': ['NCBITaxon:9606'],
            'types': ['biolink:Gene', 'biolink:GeneOrGeneProduct', 'biolink:GenomicEntity', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:PhysicalEssence', 'biolink:OntologyClass', 'biolink:BiologicalEntity', 'biolink:ThingWithTaxon', 'biolink:NamedThing', 'biolink:Entity', 'biolink:PhysicalEssenceOrOccurrent', 'biolink:MacromolecularMachineMixin', 'biolink:Protein', 'biolink:GeneProductMixin', 'biolink:Polypeptide', 'biolink:ChemicalEntityOrProteinOrPolypeptide'],
            'score': 3335.8547, 'clique_identifier_count': 11
        }],
        'FSH': [{
            'curie': 'GTOPDB:4386', 'label': 'FSH', 'highlighting': {},
            'synonyms': ['FSH', '4384', '4377'],
            'taxa': [], 
            'types': ['biolink:SmallMolecule', 'biolink:MolecularEntity', 'biolink:ChemicalEntity', 'biolink:PhysicalEssence', 'biolink:ChemicalOrDrugOrTreatment', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:ChemicalEntityOrProteinOrPolypeptide', 'biolink:NamedThing', 'biolink:Entity', 'biolink:PhysicalEssenceOrOccurrent'],
            'score': 1296.6653, 'clique_identifier_count': 1
        }, {
            'curie': 'GTOPDB:4387', 'label': 'FSH', 'highlighting': {},
            'synonyms': ['FSH', '4385', '4378'],
            'taxa': [],
            'types': ['biolink:SmallMolecule', 'biolink:MolecularEntity', 'biolink:ChemicalEntity', 'biolink:PhysicalEssence', 'biolink:ChemicalOrDrugOrTreatment', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:ChemicalEntityOrProteinOrPolypeptide', 'biolink:NamedThing', 'biolink:Entity', 'biolink:PhysicalEssenceOrOccurrent'],
            'score': 1296.6653, 'clique_identifier_count': 1
        }, {
            'curie': 'CHEBI:81569', 'label': 'Follitropin', 'highlighting': {},
            'synonyms': ['FSH', '3731', '3733', 'fshs', 'FSH-a', 'FSH-b', 'Bravelle', 'Fertinex', 'Metrodin', 'FSH-beta', 'Follitrin', 'FSH alpha', 'rFSH-alpha', 'Follitropin', 'FOLLITROPIN', 'follitropin'],
            'taxa': [],
            'types': ['biolink:SmallMolecule', 'biolink:MolecularEntity', 'biolink:ChemicalEntity', 'biolink:PhysicalEssence', 'biolink:ChemicalOrDrugOrTreatment', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:ChemicalEntityOrProteinOrPolypeptide', 'biolink:NamedThing', 'biolink:Entity', 'biolink:PhysicalEssenceOrOccurrent', 'biolink:Drug', 'biolink:OntologyClass', 'biolink:MolecularMixture', 'biolink:ChemicalMixture'],
            'score': 39.48553, 'clique_identifier_count': 148
        }],
        'delta like non-canonical Notch ligand 1': [{
            'curie': 'NCBIGene:8788', 'label': 'DLK1', 'highlighting': {},
            'synonyms': ['DLK', 'pG2', 'ZOG', 'FA1', 'DLK1', 'PREF1', 'DLK-1', 'Delta1', 'Pref-1', 'DLK1 Gene', 'DLK1 gene', 'secredeltin', 'FETAL ANTIGEN 1', 'fetal antigen 1', 'delta-like 1 homolog', 'PREADIPOCYTE FACTOR 1', 'preadipocyte factor 1', 'protein delta homolog 1', 'delta-like homolog (Drosophila)', 'delta-like 1 homolog (Drosophila)', 'DELTA, DROSOPHILA, HOMOLOG-LIKE 1', 'DELTA-LIKE NONCANONICAL NOTCH LIGAND 1', 'Delta-Like 1 Homolog (Drosophila) Gene', 'delta like non-canonical Notch ligand 1', 'FA1 protein, human', 'DLK1 protein, human', 'Dll1 protein, human', 'PREF1 protein, human', 'Pref-1 protein, human', 'hDLK1-A protein, human', 'fetal antigen-1, human', 'fetal antigen 1, human', 'secredeltin protein, human', 'delta-like 1 protein, human', 'preadipocyte factor 1, human', 'pre-adipocyte factor 1, human', 'A8K019_HUMAN Protein delta homolog 1 (trembl)', 'delta-like 1 homolog (Drosophila) protein, human', 'hDLK1', 'pG2 (human)', 'DLK-1 (human)', 'Protein Delta Homolog 1', 'protein delta homolog 1 (human)', 'DLK1_HUMAN Protein delta homolog 1 (sprot)'],
            'taxa': ['NCBITaxon:9606'],
            'types': ['biolink:Gene', 'biolink:GeneOrGeneProduct', 'biolink:GenomicEntity', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:PhysicalEssence', 'biolink:OntologyClass', 'biolink:BiologicalEntity', 'biolink:ThingWithTaxon', 'biolink:NamedThing', 'biolink:Entity', 'biolink:PhysicalEssenceOrOccurrent', 'biolink:MacromolecularMachineMixin', 'biolink:Protein', 'biolink:GeneProductMixin', 'biolink:Polypeptide', 'biolink:ChemicalEntityOrProteinOrPolypeptide'],
            'score': 205.67274, 'clique_identifier_count': 11
        }]
    }
    
    # Real normalized data from Stage 1 (exact from pipeline) 
    normalized_data = {
        'CHEBI:81569': {
            'id': {'identifier': 'CHEBI:81569', 'label': 'Follitropin'},
            'equivalent_identifiers': [{'identifier': 'CHEBI:81569', 'label': 'Follicle stimulating hormone'}, {'identifier': 'UNII:076WHW89TW', 'label': 'FOLLITROPIN'}, {'identifier': 'PUBCHEM.COMPOUND:62819', 'label': 'Follicle Stimulating Hormone'}],
            'type': ['biolink:SmallMolecule', 'biolink:MolecularEntity', 'biolink:ChemicalEntity', 'biolink:PhysicalEssence', 'biolink:ChemicalOrDrugOrTreatment', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:ChemicalEntityOrProteinOrPolypeptide', 'biolink:NamedThing', 'biolink:PhysicalEssenceOrOccurrent', 'biolink:Drug', 'biolink:OntologyClass', 'biolink:MolecularMixture', 'biolink:ChemicalMixture'],
            'information_content': 84.8
        },
        'UniProtKB:P80370': {
            'id': {'identifier': 'NCBIGene:8788', 'label': 'DLK1'},
            'equivalent_identifiers': [{'identifier': 'NCBIGene:8788', 'label': 'DLK1'}, {'identifier': 'ENSEMBL:ENSG00000185559', 'label': 'DLK1 (Hsap)'}, {'identifier': 'HGNC:2907', 'label': 'DLK1'}],
            'type': ['biolink:Gene', 'biolink:GeneOrGeneProduct', 'biolink:GenomicEntity', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:PhysicalEssence', 'biolink:OntologyClass', 'biolink:BiologicalEntity', 'biolink:ThingWithTaxon', 'biolink:NamedThing', 'biolink:PhysicalEssenceOrOccurrent', 'biolink:MacromolecularMachineMixin', 'biolink:Protein', 'biolink:GeneProductMixin', 'biolink:Polypeptide', 'biolink:ChemicalEntityOrProteinOrPolypeptide'],
            'information_content': 83.6
        }
    }
    
    # Real synonyms data from Stage 2 (exact from pipeline) - Note: No data for UniProtKB:P80370
    synonyms_data = {
        'CHEBI:81569': {
            'curie': 'CHEBI:81569',
            'preferred_name': 'Follitropin',
            'names': ['FSH', '3731', '3733', 'fshs', 'FSH-a', 'FSH-b', 'Bravelle', 'Fertinex', 'Metrodin', 'FSH-beta', 'Follitrin', 'FSH alpha', 'rFSH-alpha', 'Follitropin', 'FOLLITROPIN', 'follitropin'],
            'names_exactish': ['FSH', '3731', '3733', 'fshs', 'FSH-a', 'FSH-b', 'Bravelle', 'Fertinex', 'Metrodin', 'FSH-beta', 'Follitrin', 'FSH alpha', 'rFSH-alpha', 'Follitropin', 'FOLLITROPIN', 'follitropin'],
            'types': ['biolink:SmallMolecule', 'biolink:MolecularEntity', 'biolink:ChemicalEntity', 'biolink:PhysicalEssence', 'biolink:ChemicalOrDrugOrTreatment', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:ChemicalEntityOrProteinOrPolypeptide', 'biolink:NamedThing', 'biolink:Entity', 'biolink:PhysicalEssenceOrOccurrent', 'biolink:Drug', 'biolink:OntologyClass', 'biolink:MolecularMixture', 'biolink:ChemicalMixture'],
            'taxa': []
        },
        'NCBIGene:8788': {
            'curie': 'NCBIGene:8788',
            'preferred_name': 'DLK1',
            'names': ['DLK', 'pG2', 'ZOG', 'FA1', 'DLK1', 'PREF1', 'DLK-1', 'Delta1', 'Pref-1', 'DLK1 Gene', 'DLK1 gene', 'secredeltin', 'FETAL ANTIGEN 1', 'fetal antigen 1', 'delta-like 1 homolog', 'PREADIPOCYTE FACTOR 1', 'preadipocyte factor 1', 'protein delta homolog 1'],
            'names_exactish': ['DLK', 'pG2', 'ZOG', 'FA1', 'DLK1', 'PREF1', 'DLK-1', 'Delta1', 'Pref-1', 'DLK1 Gene', 'DLK1 gene', 'secredeltin', 'FETAL ANTIGEN 1', 'fetal antigen 1', 'delta-like 1 homolog', 'PREADIPOCYTE FACTOR 1', 'preadipocyte factor 1', 'protein delta homolog 1'],
            'types': ['biolink:Gene', 'biolink:GeneOrGeneProduct', 'biolink:GenomicEntity', 'biolink:ChemicalEntityOrGeneOrGeneProduct', 'biolink:PhysicalEssence', 'biolink:OntologyClass', 'biolink:BiologicalEntity', 'biolink:ThingWithTaxon', 'biolink:NamedThing', 'biolink:Entity', 'biolink:PhysicalEssenceOrOccurrent', 'biolink:MacromolecularMachineMixin', 'biolink:Protein', 'biolink:GeneProductMixin', 'biolink:Polypeptide', 'biolink:ChemicalEntityOrProteinOrPolypeptide'],
            'taxa': ['NCBITaxon:9606']
        }
    }
    
    # Run Stage 4
    classification, debug_info = stage4_classification_logic(
        edge, lookup_cache, normalized_data, synonyms_data
    )
    
    # EXPECTED RESULTS:
    # This edge should logically be "ambiguous" because:
    # - FSH has multiple matches (CHEBI:81569, GTOPDB:4386, GTOPDB:4387) 
    # - DLK1 has a clear match (NCBIGene:8788)
    # - The text contains both "FSH" and "DLK1" synonyms
    # However, the current pipeline classifies it as "bad" due to missing synonyms for UniProtKB:P80370
    
    print(f"✅ Stage 4 classification result: {classification}")
    print(f"   Debug info: {debug_info}")
    
    # This assertion should FAIL to demonstrate the discrepancy 
    assert classification == 'ambiguous', f"Expected 'ambiguous', got '{classification}'"
    
    # Verify debug info contains expected details
    assert debug_info['subject_curie'] == 'CHEBI:81569'
    assert debug_info['object_curie'] == 'UniProtKB:P80370'
    assert 'FSH furthermore directly upregulated expression' in debug_info['edge_text']


def test_stage4_unambiguous_case():
    """Test Stage 4 with a hypothetical case where both entities have single matches."""
    
    # Edge with unique synonyms that don't create ambiguity
    edge = {
        'subject': 'NCBIGene:8788',
        'object': 'NCBIGene:8788', 
        'sentences': 'DLK1 protein expression increased significantly.'
    }
    
    # Lookup cache with only single matches
    lookup_cache = {
        'DLK1': [
            {
                'curie': 'NCBIGene:8788',
                'label': 'DLK1',
                'synonyms': ['DLK1', 'FA1', 'PREF1'],
                'types': ['Gene'],
                'taxa': ['NCBITaxon:9606']
            }
        ]
    }
    
    normalized_data = {
        'NCBIGene:8788': {
            'id': {'identifier': 'NCBIGene:8788', 'label': 'DLK1'},
            'equivalent_identifiers': [
                {'identifier': 'NCBIGene:8788', 'label': 'DLK1'}
            ],
            'type': ['biolink:Gene']
        }
    }
    
    synonyms_data = {
        'NCBIGene:8788': {
            'curie': 'NCBIGene:8788',
            'preferred_name': 'DLK1',
            'names': ['DLK1', 'FA1', 'PREF1'],
            'types': ['Gene']
        }
    }
    
    # Run Stage 4
    classification, debug_info = stage4_classification_logic(
        edge, lookup_cache, normalized_data, synonyms_data
    )
    
    print(f"✅ Unambiguous case classification: {classification}")
    
    # Should be GOOD since DLK1 has only one match that equals the original entity
    assert classification == 'good', f"Expected 'good', got '{classification}'"


def test_stage4_no_synonyms_in_text():
    """Test Stage 4 when no entity synonyms are found in text - should be BAD."""
    
    edge = {
        'subject': 'GTOPDB:4386',
        'object': 'NCBIGene:8788',
        'sentences': 'Compound X increased protein Y expression levels.'  # No FSH or DLK1
    }
    
    # Empty lookup cache (no synonyms found in text)
    lookup_cache = {}
    
    normalized_data = {
        'GTOPDB:4386': {'id': {'identifier': 'GTOPDB:4386', 'label': 'FSH'}},
        'NCBIGene:8788': {'id': {'identifier': 'NCBIGene:8788', 'label': 'DLK1'}}
    }
    
    synonyms_data = {
        'GTOPDB:4386': {'names': ['FSH'], 'types': ['SmallMolecule']},
        'NCBIGene:8788': {'names': ['DLK1'], 'types': ['Gene']}
    }
    
    # Run Stage 4
    classification, debug_info = stage4_classification_logic(
        edge, lookup_cache, normalized_data, synonyms_data
    )
    
    print(f"✅ No synonyms in text classification: {classification}")
    
    # Should be BAD since no entity synonyms were found in the supporting text
    assert classification == 'bad', f"Expected 'bad', got '{classification}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
