# TMKP Edge Quality Control System

This system performs quality control on knowledge graph edges extracted from biomedical literature using text mining. The system focuses on identifying whether entities mentioned in edges are correctly identified in the supporting text.

## Overview

The system implements a two-phase approach:

**Phase 1** (implemented): Entity identification validation
- Checks if subject and object entities from edges are mentioned in supporting text
- Uses node normalization and synonym lookup to handle entity name variations
- Classifies edges as good, bad, or ambiguous based on entity identification

**Phase 2** (future): Relationship validation
- Will check if the relationship direction and type are correctly extracted from text

## Components

### API Functions (`api_functions.py`)
Interfaces with external APIs:
- **Node Normalizer**: Gets canonical identifiers and equivalent CURIEs for entities
- **Name Resolver**: Gets synonyms and performs name lookup for entities
- Handles batch processing and error handling

### Phase 1 Logic (`phase1.py`)
Main classification logic:
- Loads edges and nodes from JSONL files
- Collects all unique entities and normalizes them
- Gets synonyms for all entities
- For each edge, checks if entity synonyms appear in supporting text
- Classifies edges and writes results to separate files

### Web Application (`webapp.py`)
Flask-based review interface:
- Displays classified edges for human review
- Allows navigation through good, bad, and ambiguous edges
- Shows supporting text, metadata, and classification rationale
- Provides links to external databases (PubMed, ChEBI, UniProt, etc.)

### Tests
Comprehensive test suites for all components:
- `test_api_functions.py`: Tests API interaction functions
- `test_phase1.py`: Tests edge classification logic

## Setup

1. Create and activate the conda environment:
```bash
conda env create -f environment.yml
conda activate TMKP2
```

Alternatively, you can install dependencies with pip:
```bash
pip install -r requirements.txt
```

2. Ensure you have the data files:
- `tmkp_edges.jsonl`: Knowledge graph edges
- `tmkp_nodes.jsonl`: Knowledge graph nodes

## Usage

### Running Phase 1 Classification

First, activate the conda environment:
```bash
conda activate TMKP2
```

Run on a small test set first:
```bash
python phase1.py --edges tmkp_edges.jsonl --nodes tmkp_nodes.jsonl --max-edges 1000
```

Run on the full dataset:
```bash
python phase1.py --edges tmkp_edges.jsonl --nodes tmkp_nodes.jsonl
```

### Viewing Results

Start the web application:
```bash
python webapp.py
```

Then visit http://localhost:5000 to review classified edges.

### Running Tests

```bash
pytest test_api_functions.py
pytest test_phase1.py
```

## Output

Phase 1 creates three output files in the `output/` directory:
- `good_edges.jsonl`: Edges where both entities were clearly identified
- `bad_edges.jsonl`: Edges where entities could not be identified
- `ambiguous_edges.jsonl`: Edges where entity identification was uncertain

Each output edge includes:
- Original edge data
- `qc_classification`: The classification result
- `qc_phase`: Which phase performed the classification
- `edge_id`: Unique identifier for tracking

## Classification Logic

An edge is classified as:

**Good** if:
- Both subject and object entity synonyms are found in the supporting text
- The synonyms are unambiguous (map to single entities when looked up)

**Bad** if:
- No supporting text is available
- One or both entities cannot be found in the text
- Entities cannot be normalized

**Ambiguous** if:
- Entity synonyms are found but they are ambiguous (map to multiple entities)

## API Dependencies

The system relies on two external APIs:
- [Node Normalizer](https://nodenormalization-sri.renci.org/docs): For entity normalization
- [Name Resolver](https://name-resolution-sri-dev.apps.renci.org/docs): For synonym lookup

## Configuration

Key configuration options in `phase1.py`:
- `batch_size`: Number of entities to process per API call (default: 10000)
- `max_edges`: Limit for testing (processes all edges if not specified)

## Data Format

### Input Edges (JSONL)
```json
{
    "subject": "CHEBI:28748",
    "predicate": "biolink:affects", 
    "object": "UniProtKB:P18887",
    "sentences": "Doxorubicin increases XRCC1 expression...",
    "publications": ["PMID:12345678"],
    "biolink:tmkp_confidence_score": 0.95
}
```

### Input Nodes (JSONL)
```json
{
    "id": "CHEBI:28748",
    "name": "doxorubicin",
    "category": ["biolink:SmallMolecule"],
    "equivalent_identifiers": ["CHEBI:28748", "DRUGBANK:DB00997"]
}
```

## Future Enhancements

1. **Phase 2 Implementation**: Validate relationship direction and type
2. **Machine Learning Integration**: Use ML models to improve classification
3. **Manual Review Interface**: Allow reviewers to correct classifications
4. **Batch Processing**: Better support for very large datasets
5. **Caching**: Cache API responses to improve performance