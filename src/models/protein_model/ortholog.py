from models.protein_model.protein import Protein
from models.organism import Organism

class Ortholog(Protein):
    """
    Represents a non-human ortholog with sequence and structure information.

    Attributes:
        id (str): UniProt ID.
        organism (Organism): Organism of protein (human).
        name (str): Name of protein.
        string_id (str): STRING database ID.
        file_name (Path): Path to this protein's directory.
        seq (str): Path to .fasta containing amino acid sequence.
        annotations (dict): Protein annotations.
        annotations_path (str): Path to .gff containing annotations.
        pred_pdb (str): Path to predicted structure PDB.
        pred_pdb_id (str): AlphaFold ID.
        structure_file (str): Path to PDB file.
        similarity (float): % similarity to human protein.
        rmsd (float): RMSD of against human protein.
        fasta (str): FASTA sequence.
    """

    def __init__(self, id: str, organism: Organism, name: str, seq: str, annotations: str, pred_pdb: str, 
                 pred_pdb_content, string_id: str, fasta: str):
        """
        Constructor for Ortholog.

        Args:
            id (str): UniProt ID.
            organism (Organism): Organism of protein.
            name (str): Name of protein.
            seq (str): Path to .fasta containing amino acid sequence.
            annotations (str): Protein annotations.
            pred_pdb (str): Path to predicted structure PDB.
            pred_pdb_content: 3d coordinates of protein.
            string_id (str): STRING database ID.
            fasta (str): FASTA sequence.
        """
        super().__init__(id=id, organism=organism, name=name, seq=seq, annotations=annotations, pred_pdb=pred_pdb, 
                         pred_pdb_content=pred_pdb_content, string_id=string_id, fasta=fasta)
        self.similarity = None
    
    @classmethod
    def from_uniprot_result(cls, protein_name, uniprot_results, af_results, annotations_text, organism, fasta):
        id=uniprot_results['primaryAccession']
        name=protein_name
        seq=uniprot_results['sequence']['value']

        pred_pdb = af_results['file_name']
        pred_pdb_content = af_results['content']
        
        string_id=[entry["id"] for entry in uniprot_results['uniProtKBCrossReferences'] if entry["database"] == "STRING"]


        return cls(id=id, 
                   organism=organism, 
                   name=name, 
                   pred_pdb=pred_pdb,
                   pred_pdb_content=pred_pdb_content,
                   seq=seq,
                   annotations=annotations_text,
                   string_id=string_id,
                   fasta=fasta)
        
    @classmethod
    def from_ncbi_result(cls, protein_name, protein_id, organism, fasta):
        id=protein_id
        name=protein_name
        return cls(id=id, 
                   organism=organism, 
                   name=name, 
                   pred_pdb=None,
                   pred_pdb_content=None,
                   seq=fasta.split('\n', 1)[1].strip(),
                   annotations=None,
                   string_id=None,
                   fasta=fasta)
    
    def set_similarity(self, similarity: float):
        '''
        Sets similarity field.

        Args:
            similarity (float): the similarity value to set to.
        '''
        self.similarity = similarity
    
    def set_rmsd(self, rmsd: float):
        '''
        Sets rmsd field.

        Args:
            rmsd (float): the RMSD value to set to.
        '''
        self.rmsd = rmsd