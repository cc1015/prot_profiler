from client.uniprot_client import UniProtClient
from client.alphafold_client import AlphaFoldClient
from client.string_client import StringClient
from client.ncbi_client import NCBIClient
from client.therasabdab_client import TherasabdabClient
from models.protein_model.human_protein import HumanProtein
from models.protein_model.ortholog import Ortholog
from models.protein_model.protein import Protein
from models.organism import Organism
from ortholog_finders.ncbi_ortholog_finder import NCBIOrthologFinder
from ortholog_finders.uniref_ortholog_finder import UniRefOrthologFinder

class Driver:
    def __init__(self, protein_id):
        self.uniprot_client = UniProtClient()
        self.af_client = AlphaFoldClient()
        self.string_client = StringClient()
        self.ncbi_client = NCBIClient()
        self.therasabdab_client = TherasabdabClient()
        self.ncbi_ortholog_finder = NCBIOrthologFinder()
        self.uniref_ortholog_finder = UniRefOrthologFinder()
        self._set_protein_information(protein_id)
    
    def _set_protein_information(self, protein_id):
        self.protein_information = {o: None for o in Organism}
        human_data =  self.uniprot_client.get_entry(protein_id)
        self.protein_information[Organism.HUMAN] = human_data
    
    def drive(self, protein_name, protein_id):
        gene_id = next(entry["id"] for entry in self.protein_information[Organism.HUMAN]['uniProtKBCrossReferences'] 
               if entry["database"] == "GeneID")
        excluded = Organism.HUMAN
        organism_list = [o.tax_id for o in Organism if o != excluded]
        
        ncbi_ids = self.ncbi_ortholog_finder.get_orthologs(gene_id, organism_list)
        
        for organism, (label, id) in ncbi_ids.items():
            o = next((o for o in Organism if str(o.tax_id) == organism), None)
            if 'uniprot' in label:
                self.protein_information[o] = self.uniprot_client.get_entry(id)
            elif 'ncbi' in label:
                self.protein_information[o] = self.ncbi_client.get_entry(id)
        
        for organism, data in self.protein_information.items():
            if not data:
                data = self.uniref_ortholog_finder.get_ortholog_ids(protein_id, organism)
                self.protein_information[organism] = data
        
        return self._create_proteins(protein_name, protein_id)
            
    def _create_proteins(self, protein_name, protein_id) -> dict[Organism, Protein]:
        proteins = {}
        for organism, results in self.protein_information.items():
            if organism and results:
                if 'ncbi' in results:
                    fasta = results[1]
                    protein = Ortholog.from_ncbi_result(protein_name=protein_name, protein_id=protein_id, organism=organism, fasta=fasta)
                    proteins[organism] = protein
                else:
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

    def _get_fasta_content(self, protein_id) -> str:
        return self.uniprot_client.get_fasta(protein_id=protein_id)
    
    def _get_annotations_text(self, protein_id) -> str:
        result = self.uniprot_client.get_annotations(protein_id=protein_id)
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
    
    def _get_therasabdab_info(self, protein_name):
        return self.therasabdab_client.fetch(protein_name)
    
    def _choose_ortholog_selection(organism_str, uniref_accessions, search):
        prompt = f"Found multiple {organism_str} orthologs. Please select the desired ortholog from the following:\n"
        for uniref_accession in uniref_accessions:
            prompt += f"{uniref_accession}\n"
        for entry in search:
            prompt += f"{entry['primaryAccession']}\n"
        return input(prompt+"Chosen ortholog: ").strip().lower()