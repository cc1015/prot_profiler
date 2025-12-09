from collections import defaultdict
from pathlib import Path
from abc import ABC
from models.organism import Organism
from models.annotation import Annotation
from pymol import cmd
from utils.file_utils import ensure_directory, safe_write_text, safe_write_bytes

class Protein(ABC):
    """
    Represents an abstract Protein object with sequence and structure information.

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
        fasta (str): FASTA sequence.
    """

    def __init__(self, id: str, organism: Organism, name: str, seq: str, annotations: str, pred_pdb: str, pred_pdb_content, string_id: str, fasta: str):
        """
        Constructor for Protein.

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
        self.id = id
        self.organism = organism
        self.name = name
        self.string_id = string_id

        project_root = Path(__file__).parent.parent.parent.parent
        self.file_name = project_root / f"output_{name}" / f"{self.organism.name.lower()}_{self.name}"
        ensure_directory(self.file_name)

        self._set_save_seq(fasta)
        self._set_save_annotations(annotations)
        self._set_save_af_pdb(pred_pdb, pred_pdb_content)
    
    def annotate_3d_structure(self) -> str:
        """
        Annotates 3d structure of this Protein using Pymol and takes snapshot.

        Returns:
            str: Path to snapshot of annotated 3d structure.
        """
        cmd.load(self.pred_pdb)

        for annotation, idxs in self.annotations.items():
            for (start, end) in idxs:
                cmd.color(annotation.color, f"resi {start}-{end}")
        
        cmd.orient()
        png_path = self.file_name / f"{self.name}_structure_ss.png"
        pse_path = self.file_name / f"{self.name}_annotated_structure.pse"
        cmd.png(str(png_path), width=2000, ray=1)
        cmd.save(str(pse_path))
        cmd.delete("all")
        return str(png_path)
    
    def structure_align(self, mobile_proteins) -> dict:
        """
        Aligns 3d structure of given protein against this Protein. Prioritizes aligning domains of interest with corresponding annotations. 
        If none exist, aligns according to this Protein's annotations.

        Args:
            mobile_proteins (list): the mobile proteins to align.

        Returns:
            dict: calculated RMSDs after alignment.
        """
        pse_path = self.file_name.parent / "alignments.pse"
        target_path = self.pred_pdb
        target = self.organism.name + "_" + self.id
        (target_start, target_end) = (1, self.passport_table_data['length'])
            
        if (self.annotations.get(Annotation.ECD) or self.annotations.get(Annotation.CHAIN)):
            (target_start, target_end) = (self.passport_table_data['length'], 1)
            for (start, end) in (self.annotations.get(Annotation.ECD) or self.annotations.get(Annotation.CHAIN)):
                target_start = min(target_start, int(start))
                target_end = max(target_end, int(end))

        cmd.load(target_path, target)

        cmd.select(f"{target}_sele", f"{target} and resi {target_start}-{target_end}")
        cmd.create(f"{target}_chain", f"{target}_sele")
        cmd.delete(f"{target}_sele")
        cmd.delete(f"{target}")

        rmsd_dict = {}

        for mobile_protein in mobile_proteins:
            if mobile_protein.from_ncbi:
                continue
            mobile_path = mobile_protein.pred_pdb
            mobile = mobile_protein.organism.name + "_" + mobile_protein.id
            cmd.load(mobile_path, mobile)
            
            (mobile_start, mobile_end) = (target_start, target_end)
            
            '''
            if (mobile_protein.annotations.get(Annotation.CHAIN)):
                (mobile_start, mobile_end) = mobile_protein.annotations.get(Annotation.CHAIN)[0]
                if mobile_end == self.passport_table_data['length']:
                    mobile_end = target_end
            '''
            
            if (mobile_protein.annotations.get(Annotation.ECD)):
                (mobile_start, mobile_end) = mobile_protein.annotations.get(Annotation.ECD)[0]
                if mobile_end == self.passport_table_data['length']:
                    mobile_end = target_end

            cmd.select(f"{mobile}_sele", f"{mobile} and resi {mobile_start}-{mobile_end}")
            cmd.create(f"{mobile}_chain", f"{mobile}_sele")
            cmd.delete(f"{mobile}_sele")
            cmd.delete(f"{mobile}")
        
            result = cmd.align(f"polymer and name CA and {mobile}_chain", f"polymer and name CA and {target}_chain")
            mobile_protein.set_rmsd(round(result[0], 2))

            png_path = self.file_name.parent / "structure_alignment_images" / f"{mobile}_human_aligned_ss.png"
            ensure_directory(png_path.parent)
            
            cmd.disable("all")
            cmd.enable(mobile)
            cmd.enable(target)
            cmd.color("green", target)
            cmd.zoom()
            cmd.png(str(png_path), width=3000, ray=1)
            cmd.save(str(pse_path))

            rmsd_dict[mobile_protein] = (str(png_path), round(result[0], 2))
        
        return rmsd_dict

    def _set_save_seq(self, seq):
        '''
        Saves sequence to .fasta file and sets seq field to the path of the file.

        Args:
            seq (str): Sequence.
        '''
        seq_path = self.file_name / f"{self.organism.name}_{self.id}_seq.fasta"
        safe_write_text(seq_path, seq)
        self.seq = str(seq_path)

    def _set_save_annotations(self, annotations):
        '''
        Saves annotations to .gff file and sets annotations_path and annotations field.

        Args:
            annotations (str): Annotations.
        '''
        if not annotations:
            self.annotations = {}
            return
        
        gff_text = annotations.splitlines()

        annotations_dict = defaultdict(list)
        renamed = []

        for line in gff_text:
            if line.startswith("#"):
                renamed.append(line)
                continue
            parts = line.split("\t")
            if len(parts) < 9:
                continue
            feature_type = parts[2]
            attributes = parts[8]
            
            for annotation in Annotation:
                if feature_type == annotation.feature and (annotation.attr is None or annotation.attr in attributes):
                    parts[2] = annotation.name
                    annotations_dict[annotation].append((parts[3], parts[4]))
                    renamed.append("\t".join(parts))
                    break
        gff_path = self.file_name / f"{self.id}_annotations.gff"
        safe_write_text(gff_path, "\n".join(renamed))
        self.annotations_path = str(gff_path)
        if Annotation.ECD in annotations_dict:
            annotations_dict.pop(Annotation.SIGNAL, None)
            annotations_dict.pop(Annotation.CHAIN, None)
        self.annotations = annotations_dict

    def _set_save_af_pdb(self, pdb_name, pdb_content):
        if not pdb_name:
            self.from_ncbi = True
            return
        '''
        Saves PDB content to PDB file and sets pred_pdb_id and pred_pdb field.

        Args:
            pdb_name (str): PDB file name.
            pdb_content: 3d coordinates of protein.
        '''
        pdb_path = self.file_name / pdb_name
        safe_write_bytes(pdb_path, pdb_content)
        self.pred_pdb_id = pdb_name[:-4]
        self.pred_pdb = str(pdb_path)
        self.from_ncbi = False

    