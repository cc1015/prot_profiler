import argparse
import csv
from pathlib import Path
from client.uniprot_client import UniProtClient
from client.alphafold_client import AlphaFoldClient
from client.string_client import StringClient
from models.protein_model.human_protein import HumanProtein
from models.protein_model.ortholog import Ortholog
from models.protein_model.protein import Protein
from models.organism import Organism
from models.entry import Entry
from models.image import Img

class Driver:
    uniprot_client = UniProtClient()
    af_client = AlphaFoldClient()
    string_client = StringClient()
    
    def uniprot_query(self, protein_name, protein_id) -> dict:
        uniprot_data = {o: None for o in Organism}
        
        human_data =  self.uniprot_client.fetch(protein_id, kb=True)
        uniprot_data[Organism.HUMAN] = human_data
        uniref_data = self.uniprot_client.fetch(protein_id, ref=True)
    
        protein_name = human_data['genes'][0]['geneName']['value']
        rec_name=human_data['proteinDescription']['recommendedName']['fullName']['value']

        orthologs = list(Organism)
        
           
        return uniprot_data
    
    def create_proteins(self, uniprot_data, protein_name) -> dict[Organism, Protein]:
        proteins = {}

        for organism, results in uniprot_data.items():
            if results is not None:
                fasta = self._get_fasta_content(results['primaryAccession'])
                annotations_text = self._get_annotations_text(results['primaryAccession'])
                af_pdb = self._get_af_pdb(results['primaryAccession'])
            
                if af_pdb:
                    if organism == Organism.HUMAN:
                        protein = HumanProtein.from_uniprot_result(protein_name=protein_name, uniprot_results=results, af_results=af_pdb, annotations_text=annotations_text, fasta=fasta)
                    else:
                        protein = Ortholog.from_uniprot_result(protein_name=protein_name, uniprot_results=results, af_results=af_pdb, annotations_text=annotations_text, organism=organism, fasta=fasta)
            
                    proteins[organism] = protein
        return proteins

    def _get_o

    def _get_fasta_content(self, protein_id) -> str:
        return self.uniprot_client.fetch(protein_id=protein_id, fasta=True)
    
    def _get_annotations_text(self, protein_id) -> str:
        result = self.uniprot_client.fetch(protein_id=protein_id, annotations=True)
        gff = self._json_to_gff(result, protein_id)
        return gff

    def _json_to_gff(self, json, protein_id):
        gff = "##gff-version 3\n"
        features = json.get('features')
        if features:
            for annotation in features:
                gff += f"{protein_id}\tUniProtKB\t{annotation['type']}\t"
                start = str(annotation['location']['start']['value'])
                end = str(annotation['location']['end']['value'])
                note = annotation['description']
                gff += f"{start}\t{end}\t.\t.\t.\t{note}\n"
            return gff

    def _get_af_pdb(self, protein_id) -> dict:
        return self.af_client.get_af_pdb(protein_id=protein_id)

    def _get_string_db_interactions(self, protein_name, string_id):
        return self.string_client.fetch(protein_name, string_id=string_id)