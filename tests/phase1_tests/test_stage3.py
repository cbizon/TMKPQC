#!/usr/bin/env python3
"""
Test Stage 3: Text Matching & Lookup for FSH edge.
"""

import pytest
from phase1 import stage3_text_matching_and_batch_lookup

# Wrapper to adapt old test signature to new batch function
def stage3_text_matching_and_lookup_wrapper(edge, synonyms_data):
    """Wrapper to make old tests work with new batch function."""
    # Create proper normalized cache structure
    global_normalized_cache = {}
    global_synonyms_cache = {}
    
    # For each entity in the edge, create proper cache entries
    for entity_role in ['subject', 'object']:
        entity_id = edge.get(entity_role)
        if entity_id and entity_id in synonyms_data:
            # Create normalized cache entry that points to the same ID as preferred
            global_normalized_cache[entity_id] = {
                'id': {'identifier': entity_id}
            }
            # Use the synonyms data directly
            global_synonyms_cache[entity_id] = synonyms_data[entity_id]
    
    # Call the batch function with a single edge
    lookup_cache, _ = stage3_text_matching_and_batch_lookup(
        [edge], global_normalized_cache, global_synonyms_cache)
    
    return lookup_cache


def test_stage3_fsh_edge_exact_matches():
    """Test Stage 3 with exact expected input and output for perfect matches only."""
    
    # EXACT INPUT as defined - using normalized entities
    edge = {"subject":"CHEBI:81569","predicate":"biolink:affects","object":"UniProtKB:P80370","primary_knowledge_source":"infores:text-mining-provider-targeted","publications":["PMC:9308958","PMC:9308958","PMC:9308958"],"biolink:tmkp_confidence_score":0.9913376566666666,"sentences":"In our invitro approach FSH furthermore directly upregulated expression of the non-canonical Notch ligand DLK1 establishing a link between FSH/FSHR and DLK1 that, to our knowledge, has not been reported previously.|NA|(D) FSH stimulation for 8?h on Day 8 of differentiation reduced FSHR expression and increased expression of Inhibin ? subunit (INHA), Steroidogenic Acute Regulatory Protein (StAR) and Delta Like Non-Canonical Notch Ligand (DLK1) in WT cells (black bars) but not in A189V mutant lines (light and dark gray bars).|NA|The expression of steroidogenic acute regulatory protein (StAR) and delta like non-canonical notch ligand 1 (DLK1) were also stimulated by FSH and forskolin (Fig.?1D) [FSH stimulations ANOVA, Bonferroni test, P (StAR, FSH 10?ng/ml) = 0.068, P (StAR, FSH 100?ng/ml) = 4.6E?05, P (DLK1, FSH 10?ng/ml) = 0.754, P (DLK1, FSH 100?ng/ml) = 0.002, forskolin t-test, adjusted P (StAR) = 1.34E?08,|NA","tmkp_ids":["tmkp:91b3c883a4bfff31749e96cf07c54b645c8970e00b1e0d51375f3507326bd3b2","tmkp:f412ff05026d6c987d53c91ff00142a953eaaea2206e691ddbb8840652675631","tmkp:e830a6e9dd99c46741c73a3c5e65150e000385d3d2491851354aea613a213a82"],"knowledge_level":"not_provided","agent_type":"text_mining_agent","qualified_predicate":"biolink:causes","object_aspect_qualifier":"activity_or_abundance","object_direction_qualifier":"increased"}

    synonyms_data= {
      "UniProtKB:P80370": {
        "curie": "NCBIGene:8788",
        "preferred_name": "DLK1",
        "names": [ "DLK", "pG2", "ZOG", "FA1", "DLK1", "PREF1", "DLK-1", "Delta1", "Pref-1", "DLK1 Gene", "DLK1 gene", "secredeltin", "FETAL ANTIGEN 1", "fetal antigen 1", "delta-like 1 homolog", "PREADIPOCYTE FACTOR 1", "preadipocyte factor 1", "protein delta homolog 1", "delta-like homolog (Drosophila)", "delta-like 1 homolog (Drosophila)", "DELTA, DROSOPHILA, HOMOLOG-LIKE 1", "DELTA-LIKE NONCANONICAL NOTCH LIGAND 1", "Delta-Like 1 Homolog (Drosophila) Gene", "delta like non-canonical Notch ligand 1", "FA1 protein, human", "DLK1 protein, human", "Dll1 protein, human", "PREF1 protein, human", "Pref-1 protein, human", "hDLK1-A protein, human", "fetal antigen-1, human", "fetal antigen 1, human", "secredeltin protein, human", "delta-like 1 protein, human", "preadipocyte factor 1, human", "pre-adipocyte factor 1, human", "A8K019_HUMAN Protein delta homolog 1 (trembl)", "delta-like 1 homolog (Drosophila) protein, human", "hDLK1", "pG2 (human)", "DLK-1 (human)", "Protein Delta Homolog 1", "protein delta homolog 1 (human)", "DLK1_HUMAN Protein delta homolog 1 (sprot)" ],
        "names_exactish": [ "DLK", "pG2", "ZOG", "FA1", "DLK1", "PREF1", "DLK-1", "Delta1", "Pref-1", "DLK1 Gene", "DLK1 gene", "secredeltin", "FETAL ANTIGEN 1", "fetal antigen 1", "delta-like 1 homolog", "PREADIPOCYTE FACTOR 1", "preadipocyte factor 1", "protein delta homolog 1", "delta-like homolog (Drosophila)", "delta-like 1 homolog (Drosophila)", "DELTA, DROSOPHILA, HOMOLOG-LIKE 1", "DELTA-LIKE NONCANONICAL NOTCH LIGAND 1", "Delta-Like 1 Homolog (Drosophila) Gene", "delta like non-canonical Notch ligand 1", "FA1 protein, human", "DLK1 protein, human", "Dll1 protein, human", "PREF1 protein, human", "Pref-1 protein, human", "hDLK1-A protein, human", "fetal antigen-1, human", "fetal antigen 1, human", "secredeltin protein, human", "delta-like 1 protein, human", "preadipocyte factor 1, human", "pre-adipocyte factor 1, human", "A8K019_HUMAN Protein delta homolog 1 (trembl)", "delta-like 1 homolog (Drosophila) protein, human", "hDLK1", "pG2 (human)", "DLK-1 (human)", "Protein Delta Homolog 1", "protein delta homolog 1 (human)", "DLK1_HUMAN Protein delta homolog 1 (sprot)"
        ],
        "types": [ "Gene", "GeneOrGeneProduct", "GenomicEntity", "ChemicalEntityOrGeneOrGeneProduct", "PhysicalEssence", "OntologyClass", "BiologicalEntity", "ThingWithTaxon", "NamedThing", "Entity", "PhysicalEssenceOrOccurrent", "MacromolecularMachineMixin", "Protein", "GeneProductMixin", "Polypeptide", "ChemicalEntityOrProteinOrPolypeptide" ],
        "shortest_name_length": 3,
        "clique_identifier_count": 11,
        "taxa": [
          "NCBITaxon:9606"
        ],
        "curie_suffix": 8788,
        "id": "7de567ad-9d14-4421-adba-1b4854d0636a",
        "_version_": 1842245137310154752
      },
      "CHEBI:81569": {
        "curie": "CHEBI:81569",
        "preferred_name": "Follitropin",
        "names": [ "FSH", "3731", "3733", "fshs", "FSH-a", "FSH-b", "Bravelle", "Fertinex", "Metrodin", "FSH-beta", "Follitrin", "FSH alpha", "rFSH-alpha", "Follitropin", "FOLLITROPIN", "follitropin", "Metrodin HP", "MENOTROPINS", "Neo fertinorm", "UROFOLLITROPIN", "Urofollitropin", "FSH preparation", "Urofollitrophin", "Folitropina beta", "Follitropin alfa", "FOLLITROPIN ALFA", "Follitropin beta", "Folitropina alfa", "Follitrophin beta", "Urinary human FSH", "Follitropin gamma", "Follitrophin alfa", "Follitropin human", "Folitropina delta", "Follitropin delta", "Follitropin alpha", "follitropin delta", "follitropin (FSH)", "Follitrophin alpha", "Human FSH, urinary", "Metrodin high purity", "Follitropin alfa/beta", "High purity, metrodin", "FSH-Follicle stim horm", "Follotropin recombinant", "Follicle-stimulating hormone", "follicle-stimulating hormone", "follicle hormone stimulating", "FOLLICLE STIMULATING HORMONE", "Follicle-Stimulating Hormone", "follicle stimulating hormone", "Follicle stimulating hormone", "Follicle Stimulating Hormone", "follicle hormones stimulating", "Follicular stimulating hormone", "follicular stimulating hormone", "follicular hormones stimulating", "follicle stimulating fsh hormone", "FSH - Follicle stimulating hormone", "FSH (Follicle Stimulating Hormone)", "Follicle Stimulating Hormone, Human", "Pituitary follicle stimulating hormone", "Follicle stimulating hormone preparation", "Follicle stimulating hormone (FSH), pituitary", "Pituitary follicle stimulating hormone (substance)", "Recombinant human follicle stimulating hormone beta", "Recombinant human follicle-stimulating hormone (r-HFSH)", "Pituitary follicle stimulating hormone-containing product", "Product containing pituitary follicle stimulating hormone (medicinal product)", "2-[({1-[19-amino-13-(butan-2-yl)-6,9,12,15,18-pentahydroxy-7-[(C-hydroxycarbonimidoyl)methyl]-10-(1-hydroxyethyl)-16-[(4-hydroxyphenyl)methyl]-1,2-dithia-5,8,11,14,17-pentaazacycloicosa-5,8,11,14,17-pentaene-4-carbonyl]pyrrolidin-2-yl}(hydroxy)methylidene)amino]-N-[(C-hydroxycarbonimidoyl)methyl]-4-methylpentanimidate", "Gonal F", "GONAL-F", "gonal f", "gonal-f", "f gonal", "Gonal-F", "follitropin alfa 37.5 UNT/ML Injectable Solution", "Follitropin alfa 37.5 unit/mL solution for injection", "Product containing precisely follitropin alfa 37.5 unit/1 milliliter conventional release solution for injection (clinical drug)", "GONAL-F RFF KIT", "Gonal F 75 UNT Injection", "Gonal-F 75iu inj pdr+diluent", "GONAL-f RFF 75 UNT Injection", "Gonal-f RFF 75unit Powder for Injection", "follitropin alfa 75 UNT Injection [Gonal F]", "Gonal-F 75iu injection (pdr for recon)+diluent", "Follitropin Alfa 75 IU Subcutaneous Powder for Solution [GONAL-F]", "Gonal-f RFF, alpha 75 intl units subcutaneous powder for injection", "Follitropin Alfa 75 IU Subcutaneous Powder for Solution [GONAL-F RFF]", "FOLLITROPIN 75 [iU] in 1 mL SUBCUTANEOUS INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION [GONAL-F RFF]", "Follitropin alpha 150iu inj", "Recom human FSH alph 150iu inj", "follitropin alfa 300 UNT/ML Injectable Solution", "Follitropin alpha 150iu injection powder+diluent", "Follitropin alfa 300 unit/mL solution for injection", "Recomb human follicle stim horm alpha 150iu inj pdr+diluent", "follicle stimulating hormone alpha 300 intl units subcutaneous solution", "Recombinant human follicle stimulating hormone alpha 150iu injection (pdr for recon)+diluent", "Product containing precisely follitropin alfa 300 unit/1 milliliter conventional release solution for injection (clinical drug)", "Urofollitrophin 75iu inj+solv", "urofollitropin 150 UNT/ML Injectable Solution", "Urofollitropin 150 unit/mL solution for injection", "Urofollitrophin 75iu injection (pdr for recon)+solvent", "Product containing precisely urofollitropin 150 unit/1 milliliter conventional release solution for injection (clinical drug)", "follicle stimulating hormone 150 UNT/ML", "urofollitropin 150 UNT/ML", "FOLLITROPIN ALFA 450 UNIT/VIL INJ", "FOLLITROPIN ALFA 1050 UNIT/VIL INJ", "follitropin alfa 600 UNT/ML Injectable Solution", "Follitropin alfa 600 unit/mL solution for injection", "Follitropin Alfa 900 IU/1.5 ML Subcutaneous Solution", "Follitropin Alfa 450 IU/0.75 ML Subcutaneous Solution", "follitropin alfa, recombinant 450 unit SUBCUT VIAL (EA)", "follitropin alfa, recombinant@450 unit@SUBCUT@VIAL (EA)", "follitropin alfa, recombinant@1,050 unit@SUBCUT@VIAL (EA)", "follitropin alfa, recombinant 1,050 unit SUBCUT VIAL (EA)", "follicle stimulating hormone alpha 900 intl units subcutaneous solution", "follicle stimulating hormone alpha 450 intl units subcutaneous powder for injection", "Product containing precisely follitropin alfa 600 unit/1 milliliter conventional release solution for injection (clinical drug)", "Gonal-f KIT", "Gonal-f 450unit Powder for Injection", "Gonal-f 1050unit Powder for Injection", "GONAL-f 600 UNT/ML Injectable Solution", "Gonal F 600 UNT/ML Injectable Solution", "follitropin alfa 600 UNT/ML Injectable Solution [Gonal F]", "Gonal-F, 1050 intl units subcutaneous powder for injection", "Gonal-F, alpha 450 intl units subcutaneous powder for injection", "Follitropin Alfa 450 IU Subcutaneous Powder for Solution [GONAL-F]", "Follitropin Alfa 1050 IU Subcutaneous Powder for Solution [GONAL-F]", "FOLLITROPIN 450 [iU] in 1 mL SUBCUTANEOUS INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION [Gonal-f]", "FOLLITROPIN 1050 [iU] in 2 mL SUBCUTANEOUS INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION [Gonal-f]", "follitropin alfa Injectable Solution [Gonal F]", "urofollitropin Injectable Solution", "follitropin beta 150 UNT in 0.5 ML Injection", "0.5 ML follitropin beta 300 UNT/ML Injection", "follitropin beta 150 UNT per 0.5 ML Injection", "follicle stimulating hormone beta 300 intl units subcutaneous solution", "follitropin beta 300 UNT/ML", "follitropin beta 833 UNT/ML", "follitropin alfa 37.5 UNT/ML", "follitropin alfa 300 UNT/ML", "follitropin alfa 600 UNT/ML", "follitropin alfa Injectable Solution", "follitropin beta 833 UNT/ML [Follistim]", "Follitropin alpha 75iu inj", "FOLLITROPIN ALFA 75UNT/VIL INJ", "Recom human FSH alpha 75iu inj", "follitropin alfa 75 UNT Injection", "Follitropin alpha 75iu injection powder+diluent", "follitropin alfa, recombinant 75 unit SUBCUT VIAL (EA)", "follitropin alfa, recombinant@75 unit@SUBCUT@VIAL (EA)", "Follitropin Alfa 75 IU Subcutaneous Powder for Solution", "follitropin alfa, recombinant@75 unit@SUBCUT@AMPUL (EA)", "follitropin alfa, recombinant 75 unit SUBCUT AMPUL (EA)", "Recomb human follicle stim horm alpha 75iu inj pdr+diluent", "Follitropin alfa 75 unit powder for solution for injection vial", "follicle stimulating hormone alpha 75 intl units subcutaneous powder for injection", "Recombinant human follicle stimulating hormone alpha 75iu injection (pdr for recon)+diluent", "Product containing precisely follitropin alfa 75 unit/1 vial powder for conventional release solution for injection (clinical drug)", "follitropin alfa 600 UNT/ML [Gonal F]", "FOLLITROPIN BETA 300UNIT/0.36ML INJ", "0.36 ML follitropin beta 833 UNT/ML Cartridge", "follitropin beta 300 UNT in 0.36 ML Cartridge", "follitropin beta 300 IU per 0.36 ML Cartridge", "follitropin beta,recomb 300 unit/0.36 mL SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant 300 unit/0.36 mL SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant@300 unit/0.36 mL@SUBCUT@CARTRIDGE (ML)", "FOLLITROPIN BETA 600UNIT/0.72ML INJ", "follitropin beta 600 IU per 0.72 ML Cartridge", "0.72 ML follitropin beta 833 UNT/ML Cartridge", "follitropin beta 600 UNT in 0.72 ML Cartridge", "follicle stimulating hormone beta 600 intl units subcutaneous solution", "follitropin beta,recomb 600 unit/0.72 mL deliverable (833 unit/mL) SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant@600 unit/0.72 mL deliverable (833 unit/mL)@SUBCUT@CARTRIDGE (ML)", "follitropin beta,recombinant 600 unit/0.72 mL deliverable (833 unit/mL) SUBCUT CARTRIDGE (ML)", "FOLLITROPIN BETA 900UNIT/1.08ML INJ", "1.08 ML follitropin beta 833 UNT/ML Cartridge", "follitropin beta 900 UNT in 1.08 ML Cartridge", "follitropin beta 900 IU per 1.08 ML Cartridge", "follitropin beta 900 UNT per 1.08 ML Cartridge", "follitropin beta,recomb 900 unit/1.08 mL SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant 900 unit/1.08 mL SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant@900 unit/1.08 mL@SUBCUT@CARTRIDGE (ML)", "follicle stimulating hormone beta 900 intl units subcutaneous solution", "follicle stimulating hormone 52.5 UNT/ML", "follicle stimulating hormone 35 UNT/ML", "urofollitropin Injectable Product", "Urofollitropin-containing product in parenteral dose form", "Product containing urofollitropin in parenteral dose form (medicinal product form)", "follitropin alfa Injectable Product", "Follitropin alfa-containing product in parenteral dose form", "Product containing follitropin alfa in parenteral dose form (medicinal product form)", "follitropin beta Injectable Product", "Gonal F Injectable Product", "Follistim Injectable Product", "0.36 ML Follistim 833 UNT/ML Cartridge", "Follistim AQ 300 IU per 0.36 ML Cartridge", "Follistim AQ 300 UNT in 0.36 ML Cartridge", "Follistim AQ 300units Cartridge Solution for Injection", "0.36 ML follitropin beta 833 UNT/ML Cartridge [Follistim]", "Follistim AQ Cartridge, beta 300 intl units subcutaneous solution", "Follitropin Beta 300 IU/0.36 ML Subcutaneous Solution [FOLLISTIM AQ]", "follitropin 300 [iU] in 0.36 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "follitropin 350 [iU] in 0.42 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "0.72 ML Follistim 833 UNT/ML Cartridge", "Follistim AQ 600 UNT in 0.72 ML Cartridge", "Follistim AQ 600 IU per 0.72 ML Cartridge", "Follistim AQ 600units Cartridge Solution for Injection", "0.72 ML follitropin beta 833 UNT/ML Cartridge [Follistim]", "Follistim AQ Cartridge, beta 600 intl units subcutaneous solution", "Follitropin Beta 600 IU/0.72 ML Subcutaneous Solution [FOLLISTIM AQ]", "follitropin 650 [iU] in 0.78 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "follitropin 600 [iU] in 0.72 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "1.08 ML Follistim 833 UNT/ML Cartridge", "Follistim AQ 900 UNT in 1.08 ML Cartridge", "Follistim AQ 900 IU per 1.08 ML Cartridge", "Follistim AQ 900units Cartridge Solution for Injection", "1.08 ML follitropin beta 833 UNT/ML Cartridge [Follistim]", "Follistim AQ Cartridge, beta 900 intl units subcutaneous solution", "Follitropin Beta 900 IU/1.08 ML Subcutaneous Solution [FOLLISTIM AQ]", "follitropin 975 [iU] in 1.17 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "follitropin 900 [iU] in 1.08 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "1.5 ML Gonal F 600 UNT/ML Pen Injector", "GONAL-f RFF Pen 900 UNT in 1.5 ML Pen Injector", "Gonal F RFF Pen 900 UNT per 1.5 ML Pen Injector", "Gonal F RFF Redi-ject 900 UNT per 1.5 ML Pen Injector", "1.5 ML follitropin alfa 600 UNT/ML Pen Injector [Gonal F]", "Gonal-f RFF Pen, alpha 900 intl units subcutaneous solution", "Gonal-f RFF Redi-ject Pen 900unit/1.5ml Solution for Injection", "Follitropin Alfa 900 IU/1.5 ML Subcutaneous Solution [GONAL-F RFF]", "Follitropin Alfa 900 IU/1.5 ML Subcutaneous Solution [GONAL-F RFF REDI-JECT]", "FOLLITROPIN 900 [iU] in 1.5 mL SUBCUTANEOUS INJECTION, SOLUTION [Gonal-f RFF Redi-ject]", "0.75 ML Gonal F 600 UNT/ML Pen Injector", "Gonal F 450 UNT per 0.75 ML Pen Injector", "GONAL-f RFF Pen 450 UNT in 0.75 ML Pen Injector", "Gonal F RFF Redi-ject 450 UNT per 0.75 ML Pen Injector", "0.75 ML follitropin alfa 600 UNT/ML Pen Injector [Gonal F]", "Gonal-f RFF Pen, 450 intl units/0.75 mL subcutaneous solution", "Gonal-f RFF Redi-ject Pen 450unit/0.75ml Solution for Injection", "Follitropin Alfa 450 IU/0.75 ML Subcutaneous Solution [GONAL-F RFF]", "Follitropin Alfa 450 IU/0.75 ML Subcutaneous Solution [GONAL-F RFF REDI-JECT]", "FOLLITROPIN 450 [iU] in 0.75 mL SUBCUTANEOUS INJECTION, SOLUTION [Gonal-f RFF Redi-ject]", "0.5 ML Gonal F 600 UNT/ML Pen Injector", "Gonal F RFF 300 UNT per 0.5 ML Pen Injector", "GONAL-f RFF Pen 300 UNT in 0.5 ML Pen Injector", "Gonal F RFF Redi-ject 300 UNT per 0.5 ML Pen Injector", "0.5 ML follitropin alfa 600 UNT/ML Pen Injector [Gonal F]", "Gonal-f RFF Pen, alpha 300 intl units subcutaneous solution", "Gonal-f RFF Redi-ject Pen 300unit/0.5ml Solution for Injection", "Follitropin Alfa 300 IU/0.5 ML Subcutaneous Solution [GONAL-F RFF]", "Follitropin Alfa 300 IU/0.5 ML Subcutaneous Solution [GONAL-F RFF REDI-JECT]", "FOLLITROPIN 300 [iU] in 0.5 mL SUBCUTANEOUS INJECTION, SOLUTION [Gonal-f RFF Redi-ject]", "follitropin alfa Pen Injector", "FOLLITROPIN ALFA 300UNIT/0.5ML INJ PEN", "FOLLITROPIN ALFA 300UNIT/0.5ML INJ,PEN,0.5ML", "0.5 ML follitropin alfa 600 UNT/ML Pen Injector", "follitropin alfa 300 UNT in 0.5 ML Pen Injector", "follitropin alfa 300 UNT per 0.5 ML Pen Injector", "follitropin alfa, recombinant 300 unit/0.5 mL SUBCUT PEN INJECTOR (ML)", "follitropin alfa, recombinant@300 unit/0.5 mL@SUBCUT@PEN INJECTOR (ML)", "follitropin alfa Pen Injector [Gonal F]", "FOLLITROPIN ALFA 450UNIT/0.75ML INJ PEN", "FOLLITROPIN ALFA 450UNIT/0.75ML INJ,PEN,0.75ML", "follitropin alfa 450 UNT in 0.75 ML Pen Injector", "0.75 ML follitropin alfa 600 UNT/ML Pen Injector", "follitropin alfa 450 UNT per 0.75 ML Pen Injector", "follitropin alfa, recombinant@450 unit/0.75 mL@SUBCUT@PEN INJECTOR (ML)", "follitropin alfa, recombinant 450 unit/0.75 mL SUBCUT PEN INJECTOR (ML)", "follicle stimulating hormone 450 intl units/0.75 mL subcutaneous solution", "FOLLITROPIN ALFA 900UNT/1.5ML INJ PEN", "FOLLITROPIN ALFA 900UNT/1.5ML INJ,PEN,1.5ML", "1.5 ML follitropin alfa 600 UNT/ML Pen Injector", "follitropin alfa 900 UNT in 1.5 ML Pen Injector", "follitropin alfa 900 UNT per 1.5 ML Pen Injector", "follitropin alfa, recombinant@900 unit/1.5 mL@SUBCUT@PEN INJECTOR (ML)", "follitropin alfa, recombinant 900 unit/1.5 mL SUBCUT PEN INJECTOR (ML)", "follitropin beta Cartridge", "follitropin beta Cartridge [Follistim]", "follitropin alfa 75 UNT", "follitropin alfa Injection", "follitropin alfa 75 UNT [Gonal F]", "follitropin alfa Injection [Gonal F]", "follitropin beta Injection", "follicle stimulating hormone 75 UNT", "follicle stimulating hormone, porcine", "Follicle Stimulating Hormone (Porcine)", "FOLLICLE STIMULATING HORMONE (PORCINE)" ], 
    "names_exactish": [ "FSH", "3731", "3733", "fshs", "FSH-a", "FSH-b", "Bravelle", "Fertinex", "Metrodin", "FSH-beta", "Follitrin", "FSH alpha", "rFSH-alpha", "Follitropin", "FOLLITROPIN", "follitropin", "Metrodin HP", "MENOTROPINS", "Neo fertinorm", "UROFOLLITROPIN", "Urofollitropin", "FSH preparation", "Urofollitrophin", "Folitropina beta", "Follitropin alfa", "FOLLITROPIN ALFA", "Follitropin beta", "Folitropina alfa", "Follitrophin beta", "Urinary human FSH", "Follitropin gamma", "Follitrophin alfa", "Follitropin human", "Folitropina delta", "Follitropin delta", "Follitropin alpha", "follitropin delta", "follitropin (FSH)", "Follitrophin alpha", "Human FSH, urinary", "Metrodin high purity", "Follitropin alfa/beta", "High purity, metrodin", "FSH-Follicle stim horm", "Follotropin recombinant", "Follicle-stimulating hormone", "follicle-stimulating hormone", "follicle hormone stimulating", "FOLLICLE STIMULATING HORMONE", "Follicle-Stimulating Hormone", "follicle stimulating hormone", "Follicle stimulating hormone", "Follicle Stimulating Hormone", "follicle hormones stimulating", "Follicular stimulating hormone", "follicular stimulating hormone", "follicular hormones stimulating", "follicle stimulating fsh hormone", "FSH - Follicle stimulating hormone", "FSH (Follicle Stimulating Hormone)", "Follicle Stimulating Hormone, Human", "Pituitary follicle stimulating hormone", "Follicle stimulating hormone preparation", "Follicle stimulating hormone (FSH), pituitary", "Pituitary follicle stimulating hormone (substance)", "Recombinant human follicle stimulating hormone beta", "Recombinant human follicle-stimulating hormone (r-HFSH)", "Pituitary follicle stimulating hormone-containing product", "Product containing pituitary follicle stimulating hormone (medicinal product)", "2-[({1-[19-amino-13-(butan-2-yl)-6,9,12,15,18-pentahydroxy-7-[(C-hydroxycarbonimidoyl)methyl]-10-(1-hydroxyethyl)-16-[(4-hydroxyphenyl)methyl]-1,2-dithia-5,8,11,14,17-pentaazacycloicosa-5,8,11,14,17-pentaene-4-carbonyl]pyrrolidin-2-yl}(hydroxy)methylidene)amino]-N-[(C-hydroxycarbonimidoyl)methyl]-4-methylpentanimidate", "Gonal F", "GONAL-F", "gonal f", "gonal-f", "f gonal", "Gonal-F", "follitropin alfa 37.5 UNT/ML Injectable Solution", "Follitropin alfa 37.5 unit/mL solution for injection", "Product containing precisely follitropin alfa 37.5 unit/1 milliliter conventional release solution for injection (clinical drug)", "GONAL-F RFF KIT", "Gonal F 75 UNT Injection", "Gonal-F 75iu inj pdr+diluent", "GONAL-f RFF 75 UNT Injection", "Gonal-f RFF 75unit Powder for Injection", "follitropin alfa 75 UNT Injection [Gonal F]", "Gonal-F 75iu injection (pdr for recon)+diluent", "Follitropin Alfa 75 IU Subcutaneous Powder for Solution [GONAL-F]", "Gonal-f RFF, alpha 75 intl units subcutaneous powder for injection", "Follitropin Alfa 75 IU Subcutaneous Powder for Solution [GONAL-F RFF]", "FOLLITROPIN 75 [iU] in 1 mL SUBCUTANEOUS INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION [GONAL-F RFF]", "Follitropin alpha 150iu inj", "Recom human FSH alph 150iu inj", "follitropin alfa 300 UNT/ML Injectable Solution", "Follitropin alpha 150iu injection powder+diluent", "Follitropin alfa 300 unit/mL solution for injection", "Recomb human follicle stim horm alpha 150iu inj pdr+diluent", "follicle stimulating hormone alpha 300 intl units subcutaneous solution", "Recombinant human follicle stimulating hormone alpha 150iu injection (pdr for recon)+diluent", "Product containing precisely follitropin alfa 300 unit/1 milliliter conventional release solution for injection (clinical drug)", "Urofollitrophin 75iu inj+solv", "urofollitropin 150 UNT/ML Injectable Solution", "Urofollitropin 150 unit/mL solution for injection", "Urofollitrophin 75iu injection (pdr for recon)+solvent", "Product containing precisely urofollitropin 150 unit/1 milliliter conventional release solution for injection (clinical drug)", "follicle stimulating hormone 150 UNT/ML", "urofollitropin 150 UNT/ML", "FOLLITROPIN ALFA 450 UNIT/VIL INJ", "FOLLITROPIN ALFA 1050 UNIT/VIL INJ", "follitropin alfa 600 UNT/ML Injectable Solution", "Follitropin alfa 600 unit/mL solution for injection", "Follitropin Alfa 900 IU/1.5 ML Subcutaneous Solution", "Follitropin Alfa 450 IU/0.75 ML Subcutaneous Solution", "follitropin alfa, recombinant 450 unit SUBCUT VIAL (EA)", "follitropin alfa, recombinant@450 unit@SUBCUT@VIAL (EA)", "follitropin alfa, recombinant@1,050 unit@SUBCUT@VIAL (EA)", "follitropin alfa, recombinant 1,050 unit SUBCUT VIAL (EA)", "follicle stimulating hormone alpha 900 intl units subcutaneous solution", "follicle stimulating hormone alpha 450 intl units subcutaneous powder for injection", "Product containing precisely follitropin alfa 600 unit/1 milliliter conventional release solution for injection (clinical drug)", "Gonal-f KIT", "Gonal-f 450unit Powder for Injection", "Gonal-f 1050unit Powder for Injection", "GONAL-f 600 UNT/ML Injectable Solution", "Gonal F 600 UNT/ML Injectable Solution", "follitropin alfa 600 UNT/ML Injectable Solution [Gonal F]", "Gonal-F, 1050 intl units subcutaneous powder for injection", "Gonal-F, alpha 450 intl units subcutaneous powder for injection", "Follitropin Alfa 450 IU Subcutaneous Powder for Solution [GONAL-F]", "Follitropin Alfa 1050 IU Subcutaneous Powder for Solution [GONAL-F]", "FOLLITROPIN 450 [iU] in 1 mL SUBCUTANEOUS INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION [Gonal-f]", "FOLLITROPIN 1050 [iU] in 2 mL SUBCUTANEOUS INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION [Gonal-f]", "follitropin alfa Injectable Solution [Gonal F]", "urofollitropin Injectable Solution", "follitropin beta 150 UNT in 0.5 ML Injection", "0.5 ML follitropin beta 300 UNT/ML Injection", "follitropin beta 150 UNT per 0.5 ML Injection", "follicle stimulating hormone beta 300 intl units subcutaneous solution", "follitropin beta 300 UNT/ML", "follitropin beta 833 UNT/ML", "follitropin alfa 37.5 UNT/ML", "follitropin alfa 300 UNT/ML", "follitropin alfa 600 UNT/ML", "follitropin alfa Injectable Solution", "follitropin beta 833 UNT/ML [Follistim]", "Follitropin alpha 75iu inj", "FOLLITROPIN ALFA 75UNT/VIL INJ", "Recom human FSH alpha 75iu inj", "follitropin alfa 75 UNT Injection", "Follitropin alpha 75iu injection powder+diluent", "follitropin alfa, recombinant 75 unit SUBCUT VIAL (EA)", "follitropin alfa, recombinant@75 unit@SUBCUT@VIAL (EA)", "Follitropin Alfa 75 IU Subcutaneous Powder for Solution", "follitropin alfa, recombinant@75 unit@SUBCUT@AMPUL (EA)", "follitropin alfa, recombinant 75 unit SUBCUT AMPUL (EA)", "Recomb human follicle stim horm alpha 75iu inj pdr+diluent", "Follitropin alfa 75 unit powder for solution for injection vial", "follicle stimulating hormone alpha 75 intl units subcutaneous powder for injection", "Recombinant human follicle stimulating hormone alpha 75iu injection (pdr for recon)+diluent", "Product containing precisely follitropin alfa 75 unit/1 vial powder for conventional release solution for injection (clinical drug)", "follitropin alfa 600 UNT/ML [Gonal F]", "FOLLITROPIN BETA 300UNIT/0.36ML INJ", "0.36 ML follitropin beta 833 UNT/ML Cartridge", "follitropin beta 300 UNT in 0.36 ML Cartridge", "follitropin beta 300 IU per 0.36 ML Cartridge", "follitropin beta,recomb 300 unit/0.36 mL SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant 300 unit/0.36 mL SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant@300 unit/0.36 mL@SUBCUT@CARTRIDGE (ML)", "FOLLITROPIN BETA 600UNIT/0.72ML INJ", "follitropin beta 600 IU per 0.72 ML Cartridge", "0.72 ML follitropin beta 833 UNT/ML Cartridge", "follitropin beta 600 UNT in 0.72 ML Cartridge", "follicle stimulating hormone beta 600 intl units subcutaneous solution", "follitropin beta,recomb 600 unit/0.72 mL deliverable (833 unit/mL) SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant@600 unit/0.72 mL deliverable (833 unit/mL)@SUBCUT@CARTRIDGE (ML)", "follitropin beta,recombinant 600 unit/0.72 mL deliverable (833 unit/mL) SUBCUT CARTRIDGE (ML)", "FOLLITROPIN BETA 900UNIT/1.08ML INJ", "1.08 ML follitropin beta 833 UNT/ML Cartridge", "follitropin beta 900 UNT in 1.08 ML Cartridge", "follitropin beta 900 IU per 1.08 ML Cartridge", "follitropin beta 900 UNT per 1.08 ML Cartridge", "follitropin beta,recomb 900 unit/1.08 mL SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant 900 unit/1.08 mL SUBCUT CARTRIDGE (ML)", "follitropin beta,recombinant@900 unit/1.08 mL@SUBCUT@CARTRIDGE (ML)", "follicle stimulating hormone beta 900 intl units subcutaneous solution", "follicle stimulating hormone 52.5 UNT/ML", "follicle stimulating hormone 35 UNT/ML", "urofollitropin Injectable Product", "Urofollitropin-containing product in parenteral dose form", "Product containing urofollitropin in parenteral dose form (medicinal product form)", "follitropin alfa Injectable Product", "Follitropin alfa-containing product in parenteral dose form", "Product containing follitropin alfa in parenteral dose form (medicinal product form)", "follitropin beta Injectable Product", "Gonal F Injectable Product", "Follistim Injectable Product", "0.36 ML Follistim 833 UNT/ML Cartridge", "Follistim AQ 300 IU per 0.36 ML Cartridge", "Follistim AQ 300 UNT in 0.36 ML Cartridge", "Follistim AQ 300units Cartridge Solution for Injection", "0.36 ML follitropin beta 833 UNT/ML Cartridge [Follistim]", "Follistim AQ Cartridge, beta 300 intl units subcutaneous solution", "Follitropin Beta 300 IU/0.36 ML Subcutaneous Solution [FOLLISTIM AQ]", "follitropin 300 [iU] in 0.36 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "follitropin 350 [iU] in 0.42 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "0.72 ML Follistim 833 UNT/ML Cartridge", "Follistim AQ 600 UNT in 0.72 ML Cartridge", "Follistim AQ 600 IU per 0.72 ML Cartridge", "Follistim AQ 600units Cartridge Solution for Injection", "0.72 ML follitropin beta 833 UNT/ML Cartridge [Follistim]", "Follistim AQ Cartridge, beta 600 intl units subcutaneous solution", "Follitropin Beta 600 IU/0.72 ML Subcutaneous Solution [FOLLISTIM AQ]", "follitropin 650 [iU] in 0.78 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "follitropin 600 [iU] in 0.72 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "1.08 ML Follistim 833 UNT/ML Cartridge", "Follistim AQ 900 UNT in 1.08 ML Cartridge", "Follistim AQ 900 IU per 1.08 ML Cartridge", "Follistim AQ 900units Cartridge Solution for Injection", "1.08 ML follitropin beta 833 UNT/ML Cartridge [Follistim]", "Follistim AQ Cartridge, beta 900 intl units subcutaneous solution", "Follitropin Beta 900 IU/1.08 ML Subcutaneous Solution [FOLLISTIM AQ]", "follitropin 975 [iU] in 1.17 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "follitropin 900 [iU] in 1.08 mL SUBCUTANEOUS INJECTION, SOLUTION [Follistim AQ]", "1.5 ML Gonal F 600 UNT/ML Pen Injector", "GONAL-f RFF Pen 900 UNT in 1.5 ML Pen Injector", "Gonal F RFF Pen 900 UNT per 1.5 ML Pen Injector", "Gonal F RFF Redi-ject 900 UNT per 1.5 ML Pen Injector", "1.5 ML follitropin alfa 600 UNT/ML Pen Injector [Gonal F]", "Gonal-f RFF Pen, alpha 900 intl units subcutaneous solution", "Gonal-f RFF Redi-ject Pen 900unit/1.5ml Solution for Injection", "Follitropin Alfa 900 IU/1.5 ML Subcutaneous Solution [GONAL-F RFF]", "Follitropin Alfa 900 IU/1.5 ML Subcutaneous Solution [GONAL-F RFF REDI-JECT]", "FOLLITROPIN 900 [iU] in 1.5 mL SUBCUTANEOUS INJECTION, SOLUTION [Gonal-f RFF Redi-ject]", "0.75 ML Gonal F 600 UNT/ML Pen Injector", "Gonal F 450 UNT per 0.75 ML Pen Injector", "GONAL-f RFF Pen 450 UNT in 0.75 ML Pen Injector", "Gonal F RFF Redi-ject 450 UNT per 0.75 ML Pen Injector", "0.75 ML follitropin alfa 600 UNT/ML Pen Injector [Gonal F]", "Gonal-f RFF Pen, 450 intl units/0.75 mL subcutaneous solution", "Gonal-f RFF Redi-ject Pen 450unit/0.75ml Solution for Injection", "Follitropin Alfa 450 IU/0.75 ML Subcutaneous Solution [GONAL-F RFF]", "Follitropin Alfa 450 IU/0.75 ML Subcutaneous Solution [GONAL-F RFF REDI-JECT]", "FOLLITROPIN 450 [iU] in 0.75 mL SUBCUTANEOUS INJECTION, SOLUTION [Gonal-f RFF Redi-ject]", "0.5 ML Gonal F 600 UNT/ML Pen Injector", "Gonal F RFF 300 UNT per 0.5 ML Pen Injector", "GONAL-f RFF Pen 300 UNT in 0.5 ML Pen Injector", "Gonal F RFF Redi-ject 300 UNT per 0.5 ML Pen Injector", "0.5 ML follitropin alfa 600 UNT/ML Pen Injector [Gonal F]", "Gonal-f RFF Pen, alpha 300 intl units subcutaneous solution", "Gonal-f RFF Redi-ject Pen 300unit/0.5ml Solution for Injection", "Follitropin Alfa 300 IU/0.5 ML Subcutaneous Solution [GONAL-F RFF]", "Follitropin Alfa 300 IU/0.5 ML Subcutaneous Solution [GONAL-F RFF REDI-JECT]", "FOLLITROPIN 300 [iU] in 0.5 mL SUBCUTANEOUS INJECTION, SOLUTION [Gonal-f RFF Redi-ject]", "follitropin alfa Pen Injector", "FOLLITROPIN ALFA 300UNIT/0.5ML INJ PEN", "FOLLITROPIN ALFA 300UNIT/0.5ML INJ,PEN,0.5ML", "0.5 ML follitropin alfa 600 UNT/ML Pen Injector", "follitropin alfa 300 UNT in 0.5 ML Pen Injector", "follitropin alfa 300 UNT per 0.5 ML Pen Injector", "follitropin alfa, recombinant 300 unit/0.5 mL SUBCUT PEN INJECTOR (ML)", "follitropin alfa, recombinant@300 unit/0.5 mL@SUBCUT@PEN INJECTOR (ML)", "follitropin alfa Pen Injector [Gonal F]", "FOLLITROPIN ALFA 450UNIT/0.75ML INJ PEN", "FOLLITROPIN ALFA 450UNIT/0.75ML INJ,PEN,0.75ML", "follitropin alfa 450 UNT in 0.75 ML Pen Injector", "0.75 ML follitropin alfa 600 UNT/ML Pen Injector", "follitropin alfa 450 UNT per 0.75 ML Pen Injector", "follitropin alfa, recombinant@450 unit/0.75 mL@SUBCUT@PEN INJECTOR (ML)", "follitropin alfa, recombinant 450 unit/0.75 mL SUBCUT PEN INJECTOR (ML)", "follicle stimulating hormone 450 intl units/0.75 mL subcutaneous solution", "FOLLITROPIN ALFA 900UNT/1.5ML INJ PEN", "FOLLITROPIN ALFA 900UNT/1.5ML INJ,PEN,1.5ML", "1.5 ML follitropin alfa 600 UNT/ML Pen Injector", "follitropin alfa 900 UNT in 1.5 ML Pen Injector", "follitropin alfa 900 UNT per 1.5 ML Pen Injector", "follitropin alfa, recombinant@900 unit/1.5 mL@SUBCUT@PEN INJECTOR (ML)", "follitropin alfa, recombinant 900 unit/1.5 mL SUBCUT PEN INJECTOR (ML)", "follitropin beta Cartridge", "follitropin beta Cartridge [Follistim]", "follitropin alfa 75 UNT", "follitropin alfa Injection", "follitropin alfa 75 UNT [Gonal F]", "follitropin alfa Injection [Gonal F]", "follitropin beta Injection", "follicle stimulating hormone 75 UNT", "follicle stimulating hormone, porcine", "Follicle Stimulating Hormone (Porcine)", "FOLLICLE STIMULATING HORMONE (PORCINE)" ], 
    "types": [ "SmallMolecule", "MolecularEntity", "ChemicalEntity", "PhysicalEssence", "ChemicalOrDrugOrTreatment", "ChemicalEntityOrGeneOrGeneProduct", "ChemicalEntityOrProteinOrPolypeptide", "NamedThing", "Entity", "PhysicalEssenceOrOccurrent", "Drug", "OntologyClass", "MolecularMixture", "ChemicalMixture" ],
        "shortest_name_length": 3,
        "clique_identifier_count": 148,
        "curie_suffix": 81569,
        "id": "9178c712-d170-4bf2-a638-26ae2b6f7fbe",
        "_version_": 1842154207953551360
      }
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup_wrapper(edge, synonyms_data)
    
    # EXACT OUTPUT VERIFICATION
    assert isinstance(lookup_cache, dict)
    assert 'FSH' in set(lookup_cache.keys())
    assert 'DLK1' in set(lookup_cache.keys())    

    # FSH: Should have exactly 3 perfect matches with SmallMolecule type
    fsh_results = lookup_cache['FSH']
    assert len(fsh_results) == 3, f"Expected exactly 3 FSH perfect matches, got {len(fsh_results)}"
    
    # Should include CHEBI:81569, GTOPDB:4386, and GTOPDB:4387 as results
    actual_fsh_curies = {result['curie'] for result in fsh_results}
    expected_fsh_curies = {'CHEBI:81569', 'GTOPDB:4386', 'GTOPDB:4387'}
    assert actual_fsh_curies == expected_fsh_curies, f"Expected FSH CURIEs {expected_fsh_curies}, got {actual_fsh_curies}"
    
    # Verify each FSH result has exact 'FSH' synonym
    for result in fsh_results:
        synonyms = result.get('synonyms', [])
        has_exact_fsh = 'FSH' in synonyms
        assert has_exact_fsh, f"Result {result['curie']} missing exact 'FSH' synonym: {synonyms}"
        
        # Verify FSH results are SmallMolecules
        if 'types' in result:
            assert any('SmallMolecule' in t or 'Chemical' in t for t in result['types']), f"Expected SmallMolecule type for {result['curie']}"
    
    # DLK1: Should have exactly 1 perfect match with Gene type + human taxon
    dlk1_results = lookup_cache['DLK1']
    assert len(dlk1_results) == 1, f"Expected exactly 1 DLK1 perfect match, got {len(dlk1_results)}"
    
    dlk1_result = dlk1_results[0]
    assert dlk1_result['curie'] == 'NCBIGene:8788', f"Expected NCBIGene:8788, got {dlk1_result['curie']}"
    assert dlk1_result['label'] == 'DLK1', f"Expected label 'DLK1', got {dlk1_result['label']}"
    assert 'NCBITaxon:9606' in dlk1_result.get('taxa', []), "Expected human taxon in DLK1 result"
    
    # Verify DLK1 result has exact 'DLK1' synonym
    dlk1_synonyms = dlk1_result.get('synonyms', [])
    has_exact_dlk1 = 'DLK1' in dlk1_synonyms
    assert has_exact_dlk1, f"DLK1 result missing exact 'DLK1' synonym: {dlk1_synonyms}"
    
    print("✅ Stage 3 perfect match results:")
    print(f"   FSH: {len(fsh_results)} perfect matches")
    print(f"   DLK1: {len(dlk1_results)} perfect matches")


def test_stage3_no_supporting_text():
    """Test Stage 3 with no supporting text."""
    
    # Edge with no sentences
    edge = {
        'subject': 'CHEBI:81569',
        'object': 'NCBIGene:8788',
        'sentences': ''
    }
    
    synonyms_data = {
        'CHEBI:81569': {'names': ['FSH']},
        'NCBIGene:8788': {'names': ['DLK1']}
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup_wrapper(edge, synonyms_data)
    
    # Should return empty cache
    assert lookup_cache == {}
    
    print("✅ Stage 3 no text test passed")


def test_stage3_no_synonyms_found():
    """Test Stage 3 when no synonyms appear in text."""
    
    # Edge with text that doesn't contain entity synonyms
    edge = {
        'subject': 'CHEBI:81569',
        'object': 'NCBIGene:8788',
        'sentences': 'The experiment showed interesting results with compound X and protein Y.'
    }
    
    synonyms_data = {
        'CHEBI:81569': {'names': ['FSH']},
        'NCBIGene:8788': {'names': ['DLK1']}
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup_wrapper(edge, synonyms_data)
    
    # Should return empty cache
    assert lookup_cache == {}
    
    print("✅ Stage 3 no synonyms found test passed")


def test_stage3_case_insensitive_matching():
    """Test Stage 3 case-insensitive synonym matching."""
    
    # Edge with mixed case text
    edge = {
        'subject': 'CHEBI:81569',
        'object': 'NCBIGene:8788',
        'sentences': 'fsh stimulation increased dlk1 expression.'  # lowercase
    }
    
    synonyms_data = {
        'CHEBI:81569': {'names': ['FSH'], 'types': ['SmallMolecule', 'ChemicalEntity']},  # uppercase
        'NCBIGene:8788': {'names': ['DLK1'], 'types': ['Gene', 'GeneOrGeneProduct']}  # uppercase
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup_wrapper(edge, synonyms_data)
    
    # Should find both synonyms despite case differences
    found_synonyms = set(lookup_cache.keys())
    expected_synonyms = {'FSH', 'DLK1'}
    
    for expected in expected_synonyms:
        assert expected in found_synonyms, f"Case-insensitive match failed for '{expected}'"
    
    print("✅ Stage 3 case-insensitive matching test passed")


def test_stage3_data_structure():
    """Test Stage 3 returns expected data structure."""
    
    # Minimal test for structure validation
    edge = {
        'subject': 'CHEBI:81569',
        'object': 'NCBIGene:8788',
        'sentences': 'FSH affects DLK1.'
    }
    
    synonyms_data = {
        'CHEBI:81569': {'names': ['FSH'], 'types': ['SmallMolecule', 'ChemicalEntity']},
        'NCBIGene:8788': {'names': ['DLK1'], 'types': ['Gene', 'GeneOrGeneProduct']}
    }
    
    # Run Stage 3
    lookup_cache = stage3_text_matching_and_lookup_wrapper(edge, synonyms_data)
    
    # Verify data structure
    assert isinstance(lookup_cache, dict)
    
    # Each found synonym should map to a list of results
    for synonym, results in lookup_cache.items():
        assert isinstance(synonym, str), f"Synonym key should be string, got {type(synonym)}"
        assert isinstance(results, list), f"Results should be list, got {type(results)}"
        
        # Each result should be a dict with expected keys
        for result in results:
            assert isinstance(result, dict), f"Each result should be dict, got {type(result)}"
            assert 'curie' in result, f"Result missing 'curie' key: {result}"
            assert 'label' in result, f"Result missing 'label' key: {result}"
    
    print("✅ Stage 3 data structure test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
