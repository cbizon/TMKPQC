# Simple Predictions

## Goal

This system performs quality control on knowledge graph edges extracted from biomedical literature using text mining. The system focuses on identifying whether entities mentioned in edges are correctly identified in the supporting text.

## Basic Setup

* github: This project has a github repo at https://github.com/cbizon/TMKPQC 
* conda: we are using conda environment "TMKP2" (located at /opt/anaconda3/envs/TMKP2)
* tests: we are using pytest, and want to maintain high code coverage

## Input

The input data may never be changed. 

### Input Data Datasets

There are two files, a nodes (tmkp_nodes.json) and an edges (tmkp_edges.json)

Each node looks like this:
```
{"id":"CHEBI:28748","name":"doxorubicin","category":["biolink:SmallMolecule","biolink:MolecularEntity","biolink:ChemicalEntity","biolink:PhysicalEssence","biolink:ChemicalOrDrugOrTreatment","biolink:ChemicalEntityOrGeneOrGeneProduct","biolink:ChemicalEntityOrProteinOrPolypeptide","biolink:NamedThing","biolink:PhysicalEssenceOrOccurrent"],"equivalent_identifiers":["CHEBI:28748","PUBCHEM.COMPOUND:31703","CHEMBL.COMPOUND:CHEMBL53463","UNII:80168379AG","DRUGBANK:DB00997","MESH:D004317","CAS:1392315-46-6","CAS:23214-92-8","DrugCentral:960","GTOPDB:7069","HMDB:HMDB0015132","KEGG.COMPOUND:C01661","INCHIKEY:AOJJSUZBOXZQNB-TZSSRYMLSA-N","UMLS:C0013089","RXCUI:3639"],"information_content":83.1}
```
Important elements: 
- id - this is the CURIE that the TMKP has assigned to the node.  It may not be the normalized identifier.
- category: A list of categories. These are hierarchical, and the first element is the most specific, and usually the one of interest.
- equivalent_identifiers: not too important for this, but notice that each entity can have many identifiers

Each edge looks like this:
```
{"subject":"CHEBI:28748","predicate":"biolink:affects","object":"UniProtKB:P18887","primary_knowledge_source":"infores:text-mining-provider-targeted","publications":["PMID:28258155","PMID:34783124","PMID:29929045"],"biolink:tmkp_confidence_score":0.9983171550000001,"sentences":"The significant increase in CDKN1A and XRCC1 suggest a cell cycle arrest and implies an alternative NHEJ pathway in response to doxorubicin-induced DNA breaks.|NA|However, FANCD2, BRCA1 and XRCC1 foci, prominently associated with 53BP1 foci and hence DSBs resolved by cNHEJ, were only detected in doxorubicin-treated XRCC4-deficient cells.|NA","tmkp_ids":["tmkp:ae3877b6ed48c7afbc0991e8578f84513dd12cacb2bb6a485df182d33d4d4e7f","tmkp:5fd679cb1d20061fa8cbc5fab5f65c1581afd2e6436cef845ca4f2a7f95e353f","tmkp:bb27255bd16ceeab7135e5b967f5a9b28fd98024c4152a494c6c341dec11bf01","tmkp:0792c702bebbc0eea6d08d4c1b4911679ae23b03775b11345d868db6cf670fe4","tmkp:551578d2b184d7e406e3b2f81a800c880fe80a93283abbbe55e8573c2228687a"],"knowledge_level":"not_provided","agent_type":"text_mining_agent","qualified_predicate":"biolink:causes","object_aspect_qualifier":"activity_or_abundance","object_direction_qualifier":"increased"}
```
Important attributes:
- subject, object: These id's are from the nodes file
- predicate, \*qualifier.: The predicate defines the relations between the subject and object, but many edges also have things like object\_direction\_qualifier, and they are important in understanding the meaning of the edge
- sentences: these are the text from which that edge was derived.

## Basic Workflow

We are going to be looking edge by edge.  There are several phases though and we will go through them one-by-one.  

Phase 1: This is the currently implemented phase.  This phase establishes whether the subject and object are actually referenced in the text. 
Phase 2-N: These Phases will at times try to repair edges from previous phases, or apply new types of QC.

### Phase 1

Why is this difficult?  It's because (1) the name of the identifier may or may not be in the text.  Each identifier has lots of lexical synonyms.  We have ways to look those up but they require the "canonical" identifier.  (2) the identifier in the node/edge might not be the canonical identifier. And (3) The same synonym may be a synonym for different identifiers. This doesn't mean that they're the same thing, it just means that the text is ambiugous.   To deal with this, we follow the following 4 stage process.

1. **Get canonical identifier**: Use node normalization API to get the best/preferred identifier for the entity (e.g., subject). This gives us the identifier that we will use in subsequent calls.

2. **Get all synonyms**: Use the synonyms API to get all lexical synonyms for that canonical identifier. One of these synonyms should be what was actually matched in the original text. If we can't find any synonym that appears in the text, then this edge has an unresolved entity.

3. **Reverse lookup**: Now we need to see if this is the ONLY entity that hast this synonym.  Take the synonym string that we found in the text (from step 2) and send it to the lookup/bulk-lookup API to see what entities it could resolve to.  

4. **Evaluate ambiguity**: 
   - If we were not able to find text in the sentences that is a synonym for the TMKP entity -> **Unresolved Entity**
   - If lookup returns only the original subject entity → **Passed Phase 1** 
   - If we find that the same synonym applies to more than one CURIE -> **Ambiguous Entity Resolution**
Note that the string resolution is slightly subtle - there are two kinds of names. The preferred name, and the rest of the synonyms.  If there is a single entity where the text matches the preferred name, then we have a good match, even if other curies have the label as a regular synonym.  

## Key APIs

Our main tools in this are going to be two APIs.  One is nodenormalizer found here: https://nodenormalization-dev.apps.renci.org/docs#/. We are only interested in the get\_normalized\_nodes function, and especially in its POST implementation, which is much more efficient.  This function takes one CURIE and returns every other CURIE that it knows about for the same concept.  Here is an example payload:
```
{
  "curies": [
    "MESH:D014867",
    "NCIT:C34373"
  ],
  "conflate": true,
  "description": false,
  "drug_chemical_conflate": true
}
```
In this payload we are sending two curies that we want to ask about.  We are also saying to merge certain types of entities (conflation) and we always want these to be true. always.

The result of this query will look like:
```
{
  "MESH:D014867": {
    "id": {
      "identifier": "CHEBI:15377",
      "label": "Water"
    },
    "equivalent_identifiers": [
      {
        "identifier": "CHEBI:15377",
        "label": "water"
      },
      {
        "identifier": "UNII:059QF0KO0R",
        "label": "WATER"
      },
      {
        "identifier": "PUBCHEM.COMPOUND:962",
        "label": "Water"
      },
      {
        "identifier": "CHEMBL.COMPOUND:CHEMBL1098659",
        "label": "WATER"
      },
      {
        "identifier": "DRUGBANK:DB09145",
        "label": "Water"
      },
      {
        "identifier": "MESH:D014867",
        "label": "Water"
      },
      {
        "identifier": "CAS:231-791-2"
      },
      {
        "identifier": "CAS:7732-18-5"
      },
      {
        "identifier": "HMDB:HMDB0002111",
        "label": "Water"
      },
      {
        "identifier": "KEGG.COMPOUND:C00001",
        "label": "H2O"
      },
      {
        "identifier": "INCHIKEY:XLYOFNOQVPJJNP-UHFFFAOYSA-N"
      },
      {
        "identifier": "UMLS:C0043047",
        "label": "water"
      },
      {
        "identifier": "RXCUI:11295"
      }
    ],
    "type": [
      "biolink:SmallMolecule",
      "biolink:MolecularEntity",
      "biolink:ChemicalEntity",
      "biolink:PhysicalEssence",
      "biolink:ChemicalOrDrugOrTreatment",
      "biolink:ChemicalEntityOrGeneOrGeneProduct",
      "biolink:ChemicalEntityOrProteinOrPolypeptide",
      "biolink:NamedThing",
      "biolink:PhysicalEssenceOrOccurrent"
    ],
    "information_content": 47.7
  },
  "NCIT:C34373": {
    "id": {
      "identifier": "MONDO:0004976",
      "label": "amyotrophic lateral sclerosis"
    },
    "equivalent_identifiers": [
      {
        "identifier": "MONDO:0004976",
        "label": "amyotrophic lateral sclerosis"
      },
      {
        "identifier": "DOID:332",
        "label": "amyotrophic lateral sclerosis"
      },
      {
        "identifier": "orphanet:803"
      },
      {
        "identifier": "UMLS:C0002736",
        "label": "Amyotrophic Lateral Sclerosis"
      },
      {
        "identifier": "MESH:D000690",
        "label": "Amyotrophic Lateral Sclerosis"
      },
      {
        "identifier": "MEDDRA:10002026"
      },
      {
        "identifier": "MEDDRA:10052889"
      },
      {
        "identifier": "NCIT:C34373",
        "label": "Amyotrophic Lateral Sclerosis"
      },
      {
        "identifier": "SNOMEDCT:86044005"
      },
      {
        "identifier": "medgen:274"
      },
      {
        "identifier": "icd11.foundation:1982355687"
      },
      {
        "identifier": "ICD10:G12.21"
      },
      {
        "identifier": "ICD9:335.20"
      },
      {
        "identifier": "KEGG.DISEASE:05014"
      },
      {
        "identifier": "HP:0007354",
        "label": "Amyotrophic lateral sclerosis"
      }
    ],
    "type": [
      "biolink:Disease",
      "biolink:DiseaseOrPhenotypicFeature",
      "biolink:BiologicalEntity",
      "biolink:ThingWithTaxon",
      "biolink:NamedThing"
    ],
    "information_content": 74.9
  }
}
```

Notice that each entity returns a list of other identifiers.  Note also that types are returned. These are ordered, and we are always interested in the first element in the list, which should be the most specific. Note also that each input has an id element - this contains the preferred identifier for the clique of identifiers.

The other tool of interest is name resolver found here:  https://name-resolution-sri-dev.apps.renci.org/docs#.  This API has 3 functions of interest:  
1) lookup: Take a string and return possible curies that match
2) bulk-lookup: Take multiple strings and return possible curies for each (more efficient)
3) synonyms: Take a curie (which must be the preferred id from nodenorm) and return all known lexical synonyms for that curie.

Synonyms Input:
```
{
  "preferred_curies": [
    "MONDO:0005737",
    "MONDO:0009757"
  ]
}
```
Synonyms Output:
```
{
  "MONDO:0005737": {
    "curie": "MONDO:0005737",
    "names": [
      "EHF",
      "Ebola",
      "Ebola fever",
      "Ebola disease",
      "disease ebola",
      "EBOLA VIRUS DIS",
      "Ebola Infection",
      "Infection, Ebola",
      "Ebola virus disease",
      "Ebola Virus Disease",
      "ebola virus disease",
      "Ebolavirus Infection",
      "Infection, Ebolavirus",
      "Ebola Virus Infection",
      "Ebola virus infection",
      "Ebolavirus Infections",
      "ebola virus infection",
      "Infection, Ebola Virus",
      "Infections, Ebolavirus",
      "Virus Infection, Ebola",
      "Ebola Hemorrhagic Fever",
      "ebola fever hemorrhagic",
      "ebola hemorrhagic fever",
      "Ebola hemorrhagic fever",
      "Ebola haemorrhagic fever",
      "Hemorrhagic Fever, Ebola",
      "ebola haemorrhagic fever",
      "EVD - Ebola virus disease",
      "Ebolavirus infectious disease",
      "Ebola virus hemorrhagic fever",
      "Ebolavirus disease or disorder",
      "Viral hemorrhagic fever, Ebola",
      "Ebola virus disease (disorder)",
      "Viral haemorrhagic fever, Ebola",
      "Ebolavirus caused disease or disorder",
      "Ebola virus hemorrhagic fever (diagnosis)"
    ],
    "names_exactish": [
      "EHF",
      "Ebola",
      "Ebola fever",
      "Ebola disease",
      "disease ebola",
      "EBOLA VIRUS DIS",
      "Ebola Infection",
      "Infection, Ebola",
      "Ebola virus disease",
      "Ebola Virus Disease",
      "ebola virus disease",
      "Ebolavirus Infection",
      "Infection, Ebolavirus",
      "Ebola Virus Infection",
      "Ebola virus infection",
      "Ebolavirus Infections",
      "ebola virus infection",
      "Infection, Ebola Virus",
      "Infections, Ebolavirus",
      "Virus Infection, Ebola",
      "Ebola Hemorrhagic Fever",
      "ebola fever hemorrhagic",
      "ebola hemorrhagic fever",
      "Ebola hemorrhagic fever",
      "Ebola haemorrhagic fever",
      "Hemorrhagic Fever, Ebola",
      "ebola haemorrhagic fever",
      "EVD - Ebola virus disease",
      "Ebolavirus infectious disease",
      "Ebola virus hemorrhagic fever",
      "Ebolavirus disease or disorder",
      "Viral hemorrhagic fever, Ebola",
      "Ebola virus disease (disorder)",
      "Viral haemorrhagic fever, Ebola",
      "Ebolavirus caused disease or disorder",
      "Ebola virus hemorrhagic fever (diagnosis)"
    ],
    "types": [
      "Disease",
      "DiseaseOrPhenotypicFeature",
      "BiologicalEntity",
      "ThingWithTaxon",
      "NamedThing",
      "Entity"
    ],
    "preferred_name": "Ebola hemorrhagic fever",
    "shortest_name_length": 3,
    "clique_identifier_count": 15,
    "curie_suffix": 5737,
    "id": "259aaf70-b8a3-4cec-adf9-aa886867be29",
    "_version_": 1841051406731051000
  },
  "MONDO:0009757": {
    "curie": "MONDO:0009757",
    "names": [
      "NPC1",
      "NIEMANN PICK DIS TYPE D",
      "NIEMANN PICKS DIS TYPE D",
      "Niemann Pick Type D Disease",
      "Niemann-Pick disease type D",
      "Niemann pick disease type D",
      "Niemann Pick Disease Type D",
      "Niemann-Pick Disease Type D",
      "Niemann-Pick Type D Disease",
      "Niemann-Pick Disease, Type D",
      "Niemann-Pick disease, type D",
      "Niemann-Pick disease, type C",
      "Type C1 Niemann-Pick Disease",
      "Niemann-Pick disease type C1",
      "Niemann Pick Disease, Type D",
      "NIEMANN-PICK DISEASE, TYPE D",
      "type C1 Niemann-Pick disease",
      "Niemann Pick's Disease Type D",
      "Niemann-Pick's Disease Type D",
      "NIEMANN-PICK DISEASE, TYPE C1",
      "Niemann-Pick disease, type C1",
      "Niemann-Pick Disease, Type C1",
      "Niemann-PICK disease, type C1",
      "NIEMANN PICK DIS NOVE SCOTIAN",
      "Niemann Pick Disease, Type C1",
      "Niemann Pick Disease, Nova Scotian",
      "Niemann-Pick Disease, Nova Scotian",
      "Niemann-Pick disease, Nova Scotian",
      "Niemann-Pick disease, type D (disorder)",
      "Niemann-Pick disease type D (diagnosis)",
      "Niemann-Pick Disease, Nova Scotian Type",
      "Niemann-Pick disease, nova Scotian type",
      "NIEMANN-PICK DISEASE, NOVA SCOTIAN TYPE",
      "Niemann-Pick disease type C1 (diagnosis)",
      "Nova Scotia Niemann-Pick Disease (Type D)",
      "Nova Scotia Niemann Pick Disease (Type D)",
      "Niemann-Pick disease, type C, subacute form",
      "Niemann Pick disease, Subacute Juvenile Form",
      "Niemann-Pick disease, subacute juvenile form",
      "Niemann-Pick disease, Subacute Juvenile Form",
      "NIEMANN-PICK DISEASE, SUBACUTE JUVENILE FORM",
      "Niemann-Pick disease, chronic neuronopathic form",
      "Nova Scotia (Type D) Form of Niemann-Pick Disease",
      "Niemann-Pick disease, type C, subacute form (disorder)",
      "Niemann-Pick disease without sphingomyelinase deficiency",
      "Niemann-Pick disease with cholesterol esterification block",
      "neurovisceral storage disease with vertical supranuclear ophthalmoplegia"
    ],
    "names_exactish": [
      "NPC1",
      "NIEMANN PICK DIS TYPE D",
      "NIEMANN PICKS DIS TYPE D",
      "Niemann Pick Type D Disease",
      "Niemann-Pick disease type D",
      "Niemann pick disease type D",
      "Niemann Pick Disease Type D",
      "Niemann-Pick Disease Type D",
      "Niemann-Pick Type D Disease",
      "Niemann-Pick Disease, Type D",
      "Niemann-Pick disease, type D",
      "Niemann-Pick disease, type C",
      "Type C1 Niemann-Pick Disease",
      "Niemann-Pick disease type C1",
      "Niemann Pick Disease, Type D",
      "NIEMANN-PICK DISEASE, TYPE D",
      "type C1 Niemann-Pick disease",
      "Niemann Pick's Disease Type D",
      "Niemann-Pick's Disease Type D",
      "NIEMANN-PICK DISEASE, TYPE C1",
      "Niemann-Pick disease, type C1",
      "Niemann-Pick Disease, Type C1",
      "Niemann-PICK disease, type C1",
      "NIEMANN PICK DIS NOVE SCOTIAN",
      "Niemann Pick Disease, Type C1",
      "Niemann Pick Disease, Nova Scotian",
      "Niemann-Pick Disease, Nova Scotian",
      "Niemann-Pick disease, Nova Scotian",
      "Niemann-Pick disease, type D (disorder)",
      "Niemann-Pick disease type D (diagnosis)",
      "Niemann-Pick Disease, Nova Scotian Type",
      "Niemann-Pick disease, nova Scotian type",
      "NIEMANN-PICK DISEASE, NOVA SCOTIAN TYPE",
      "Niemann-Pick disease type C1 (diagnosis)",
      "Nova Scotia Niemann-Pick Disease (Type D)",
      "Nova Scotia Niemann Pick Disease (Type D)",
      "Niemann-Pick disease, type C, subacute form",
      "Niemann Pick disease, Subacute Juvenile Form",
      "Niemann-Pick disease, subacute juvenile form",
      "Niemann-Pick disease, Subacute Juvenile Form",
      "NIEMANN-PICK DISEASE, SUBACUTE JUVENILE FORM",
      "Niemann-Pick disease, chronic neuronopathic form",
      "Nova Scotia (Type D) Form of Niemann-Pick Disease",
      "Niemann-Pick disease, type C, subacute form (disorder)",
      "Niemann-Pick disease without sphingomyelinase deficiency",
      "Niemann-Pick disease with cholesterol esterification block",
      "neurovisceral storage disease with vertical supranuclear ophthalmoplegia"
    ],
    "types": [
      "Disease",
      "DiseaseOrPhenotypicFeature",
      "BiologicalEntity",
      "ThingWithTaxon",
      "NamedThing",
      "Entity"
    ],
    "preferred_name": "Niemann-Pick disease, type C1",
    "shortest_name_length": 4,
    "clique_identifier_count": 12,
    "curie_suffix": 9757,
    "id": "dcc793c5-8579-4773-a4e5-7819e0f9943b",
    "_version_": 1841051436057624600
  }
}
```

In these outputs we are interested in "names" and especially "preferred\_name".

Lookup input:
```
curl -X 'POST' \
  'https://name-resolution-sri-dev.apps.renci.org/lookup?string=doxorubicin&autocomplete=false&highlighting=false&offset=0&limit=10&biolink_type=SmallMolecule' \
  -H 'accept: application/json' \
  -d ''
```

Lookup output:
```
[
  {
    "curie": "CHEBI:28748",
    "label": "Doxorubicin",
    "highlighting": {},
    "synonyms": [
      "ADM",
      "ADR",
      "adr",
      ...
    ],
    "taxa": [],
    "types": [
      "biolink:SmallMolecule",
      "biolink:MolecularEntity",
      "biolink:ChemicalEntity",
      "biolink:PhysicalEssence",
      "biolink:ChemicalOrDrugOrTreatment",
      "biolink:ChemicalEntityOrGeneOrGeneProduct",
      "biolink:ChemicalEntityOrProteinOrPolypeptide",
      "biolink:NamedThing",
      "biolink:Entity",
      "biolink:PhysicalEssenceOrOccurrent",
      "biolink:MolecularMixture",
      "biolink:ChemicalMixture",
      "biolink:Drug",
      "biolink:OntologyClass"
    ],
    "score": 9395.258,
    "clique_identifier_count": 132
  },
  {
    "curie": "CHEBI:64816",
    "label": "doxorubicin(1+)",
    "highlighting": {},
    "synonyms": [
      "doxorubicin",
      "Doxorubicin(1+)",
      "doxorubicin(1+)",
      "doxorubicin cation",
      "(1S,3S)-3,5,12-trihydroxy-3-(hydroxyacetyl)-10-methoxy-6,11-dioxo-1,2,3,4,6,11-hexahydrotetracen-1-yl 3-azaniumyl-2,3,6-trideoxy-alpha-L-lyxo-hexopyranoside"
    ],
    "taxa": [],
    "types": [
      "biolink:SmallMolecule",
      "biolink:MolecularEntity",
      "biolink:ChemicalEntity",
      "biolink:PhysicalEssence",
      "biolink:ChemicalOrDrugOrTreatment",
      "biolink:ChemicalEntityOrGeneOrGeneProduct",
      "biolink:ChemicalEntityOrProteinOrPolypeptide",
      "biolink:NamedThing",
      "biolink:Entity",
      "biolink:PhysicalEssenceOrOccurrent"
    ],
    "score": 447.1852,
    "clique_identifier_count": 3
  },
]
```

There are other options that we will want to take advantage of, like the ability to limit to a particular biolink class or taxon (human is NCBITaxon:9606)

## Project Structure

We have three python scripts:
- api\_functions.py: python wrappers for the APIs.  Handle batching and retries
- phase1.py: The logic of the 4 stage process described above.  Takes a batched approach for efficiency.
- webapp.py: Displays the results of phase1.py for human curators

## ***RULES OF THE ROAD***

Don't use mocks. 

Ask clarifying questions

Do not implement bandaids - treat the root cause of problems

Once we have a test, do not delete it without explicit permission.  

Do not return made up results if an API fails.  Let it fail.

When changing code, don't make duplicate functions - just change the function. We can always roll back changes if needed.

Keep the directories clean, don't leave a bunch of junk laying around.
