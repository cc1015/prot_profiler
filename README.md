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
pip install streamlit pymol-open-source
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
3. Provide protein information
4. Click "Create" to start the process

The application will:
1. Retrieve protein information from UniProt
2. Find orthologs across different organisms
3. Annotate and align sequences
4. Perform structural alignments
5. Retrieve STRING DB interactions
6. Generate a PowerPoint presentation

You can cancel the process at any time using the "Cancel" button.

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

## Notes

- The application requires internet connectivity to fetch data
- Processing time depends on the number of proteins and available orthologs
- Ensure sufficient disk space for output files and structures
- PyMOL must be properly configured for 3D structure visualization

