# Protein Passport Automation
An automated tool for generating comprehensive protein analysis reports ("Protein Passports") that retrieve, analyze, and visualize protein information across multiple organisms. The application creates PowerPoint presentations containing protein sequences, structural alignments, interaction networks, and annotations.
## Features
- **Multi-source Data Retrieval**: Fetches protein data from UniProt, AlphaFold, STRING DB, NCBI, and Therasabdab
- **Ortholog Finding**: Automatically identifies orthologs across multiple organisms:
  - Human (Homo sapiens)
  - Mouse (Mus musculus)
  - Alpaca (Vicugna pacos)
  - Cynomolgus monkey (Macaca fascicularis)
  - Chicken (Gallus gallus)
  - Rabbit (Oryctolagus cuniculus)
  - Llama (Lama glama)
- **Custom Organisms**: Add your own organisms by providing scientific name and NCBI taxonomic ID
- **Sequence Analysis**: Annotates and aligns protein sequences using Geneious
- **Structural Analysis**:
  - Retrieves AlphaFold predicted structures
  - Annotates 3D structures with domain information
  - Performs structural alignments and calculates RMSD values
- **Interaction Networks**: Retrieves protein-protein interaction data from STRING DB
- **Automated Report Generation**: Creates PowerPoint presentations with all analysis results
## Requirements
- Python 3.x
- Streamlit
- PyMOL (for 3D structure visualization)
- Geneious (for sequence annotation and alignment)
- Required Python packages (see Installation)
## Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd protein_passport_automation
```
2. Install required Python packages:
```bash
conda create --name <env_name>
conda activate <env_name>
conda install -c conda-forge -c schrodinger pymol-bundle
pip install streamlit python-pptx requests bs4
```
Note: Additional dependencies may be required. Check the import statements in the source files for a complete list.
3. Ensure PyMOL and Geneious are installed and accessible in your system PATH.
## Usage
### Running the Application
Start the Streamlit web application:
```bash
streamlit run src/main.py
```
The application will open in your default web browser.
### Input Methods
1. **Single Entry**: Enter a protein name and UniProt accession ID manually
2. **CSV Upload**: Upload a CSV file with columns:
  - `protein_name`: Name of the protein
  - `protein_id`: UniProt accession ID
### Process Flow
1. Enter your first and last name
2. Choose input method (Single Entry or CSV Upload)
3. Select organisms to use as orthologs (all selected by default)
4. Optionally add custom organisms with scientific name and taxonomic ID
5. Provide protein information
6. Click "Create" to start the process
The application will:
1. Retrieve protein information from UniProt
2. Find orthologs across different organisms (see [Ortholog Finding Process](#ortholog-finding-process))
3. Annotate and align sequences
4. Perform structural alignments
5. Retrieve STRING DB interactions
6. Generate a PowerPoint presentation
You can cancel the process at any time using the "Cancel" button.
### Organism Selection
- **Predefined Organisms**: Checkboxes for all available organisms (all selected by default)
- **Custom Organisms**:
 - Enter scientific name (e.g., "Canis lupus")
 - Enter NCBI taxonomic ID (e.g., 9615)
 - Click "Add Custom Organism" to add it to your list
 - Custom organisms can be selected/deselected and removed individually
### Ortholog Finding Process
The program uses a two-step approach to find UniProt entries for orthologs:
#### Step 1: NCBI Ortholog Finder (Primary Method)
1. **Extract Gene ID**: The program extracts the NCBI GeneID from the human UniProt entry's cross-references.
2. **Query NCBI Ortholog API**:
  - Uses the NCBI Datasets API (`/datasets/v2/gene/id/{gene_id}/orthologs`) to find ortholog genes
  - Filters by the taxonomic IDs of selected organisms
  - Returns a list of ortholog gene reports
3. **Find Protein References**:
  - For each ortholog gene found, the program scrapes the NCBI Gene page
  - Searches for protein reference sequences in priority order:
    1. **UniProtKB/Swiss-Prot** entries (curated, highest quality)
    2. **UniProtKB/TrEMBL** entries (unreviewed but in UniProt)
    3. **RefSeq** entries (NCBI protein database, fallback)
  - Returns a tuple indicating the source: `('uniprot', uniprot_id)` or `('ncbi', refseq_id)`
4. **Retrieve Protein Data**:
  - If a UniProt ID is found, retrieves the full UniProt entry via UniProt API
  - If only a RefSeq ID is found, retrieves the FASTA sequence from NCBI
#### Step 2: UniRef Ortholog Finder (Fallback Method)
For organisms not found via NCBI, the program uses UniRef clusters:
1. **Query UniRef Cluster**:
  - Retrieves the UniRef cluster data for the human protein
  - Searches cluster members for entries matching:
    - The target organism's taxonomic ID
    - The same protein name (recommended name)
2. **Verify and Retrieve**:
  - If found in UniRef cluster, retrieves the UniProt entry
  - Cross-references with a UniProtKB search to verify correctness
  - If multiple matches exist, selects the first result automatically
3. **Direct UniProtKB Search** (if not in UniRef):
  - Performs a search in UniProtKB using:
    - Protein recommended name
    - Gene name
    - Organism taxonomic ID
  - Returns the first matching result
#### Result Processing
- **UniProt Entries**: Full protein data including sequence, annotations, cross-references, and AlphaFold structures
- **NCBI RefSeq Entries**: FASTA sequence only (no structure data available)
- **Missing Orthologs**: If no ortholog is found for a selected organism, it is skipped in the final output
This dual-method approach ensures maximum coverage: NCBI provides high-quality ortholog relationships, while UniRef/UniProtKB search catches cases where NCBI data is incomplete or unavailable.
## Output
The application generates:
- **PowerPoint Presentation**: A comprehensive report containing:
 - Protein information table with annotated 3D structure
 - Human protein sequence slide
 - Structural alignment slides with RMSD values
 - STRING DB interaction network
- **Output Files**: Organized in `output_<protein_name>/` directories:
 - FASTA sequence files
 - GFF annotation files
 - PDB structure files
 - PNG images of structures and alignments
 - PyMOL session files
## Technical Details
### Ortholog Finding Strategy
The program employs a hierarchical approach to maximize ortholog discovery:
1. **NCBI First**: Uses NCBI's curated ortholog database for reliable gene-level ortholog relationships
2. **UniRef Fallback**: Uses UniRef clusters to find sequence-similar proteins when NCBI data is unavailable
3. **UniProtKB Search**: Direct search as final fallback for edge cases
This ensures that even if an organism isn't in NCBI's ortholog database, the program can still find related proteins through sequence similarity.
### Data Sources Priority
When multiple protein references are available, the program prioritizes:
1. UniProtKB/Swiss-Prot (curated, reviewed)
2. UniProtKB/TrEMBL (unreviewed but in UniProt)
3. NCBI RefSeq (fallback, sequence only)
## Notes
- The application requires internet connectivity to fetch data from external APIs
- Processing time depends on the number of proteins and available orthologs
- Ensure sufficient disk space for output files and structures
- PyMOL must be properly configured for 3D structure visualization
- Custom organisms require valid NCBI taxonomic IDs - verify IDs at [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy)
- Some organisms may not have orthologs available in databases - these will be skipped automatically