from client.uniprot_client import UniProtClient
from client.alphafold_client import AlphaFoldClient
from client.string_client import StringClient
from client.ncbi_client import NCBIClient
from client.therasabdab_client import TherasabdabClient
from models.protein_model.human_protein import HumanProtein
from models.protein_model.ortholog import Ortholog
from models.protein_model.protein import Protein
from models.organism import Organism, CustomOrganism
from ortholog_finders.ncbi_ortholog_finder import NCBIOrthologFinder
from ortholog_finders.uniref_ortholog_finder import UniRefOrthologFinder

class Driver:
    def __init__(self, protein_id, custom_organisms=None):
        self.uniprot_client = UniProtClient()
        self.af_client = AlphaFoldClient()
        self.string_client = StringClient()
        self.ncbi_client = NCBIClient()
        self.therasabdab_client = TherasabdabClient()
        self.ncbi_ortholog_finder = NCBIOrthologFinder()
        self.uniref_ortholog_finder = UniRefOrthologFinder()
        self._set_protein_information(protein_id, custom_organisms)
    
    def _set_protein_information(self, protein_id, custom_organisms=None):
        # Initialize with all predefined organisms
        self.protein_information = {o: None for o in Organism}
        # Add custom organisms if provided
        if custom_organisms:
            for custom_org in custom_organisms:
                self.protein_information[custom_org] = None
        human_data =  self.uniprot_client.get_entry(protein_id)
        self.protein_information[Organism.HUMAN] = human_data
    
    def drive(self, protein_name, protein_id, selected_organisms=None):
        gene_id = next(entry["id"] for entry in self.protein_information[Organism.HUMAN]['uniProtKBCrossReferences'] 
               if entry["database"] == "GeneID")
        excluded = Organism.HUMAN
        
        # Use selected organisms if provided, otherwise use all organisms except HUMAN
        if selected_organisms is None:
            organisms_to_process = [o for o in Organism if o != excluded]
        else:
            organisms_to_process = selected_organisms
        
        organism_list = [o.tax_id for o in organisms_to_process]
        
        ncbi_ids = self.ncbi_ortholog_finder.get_orthologs(gene_id, organism_list)
        
        # Create a mapping of tax_id to organism for both predefined and custom organisms
        tax_id_to_organism = {}
        for org in organisms_to_process:
            tax_id_to_organism[str(org.tax_id)] = org
        
        for organism_tax_id, (label, id) in ncbi_ids.items():
            o = tax_id_to_organism.get(organism_tax_id)
            # Only process if this organism is in the selected list (or if no selection was made)
            if o and (selected_organisms is None or o in selected_organisms):
                if 'uniprot' in label:
                    self.protein_information[o] = self.uniprot_client.get_entry(id)
                elif 'ncbi' in label:
                    self.protein_information[o] = self.ncbi_client.get_entry(id)
        
        # Only process selected organisms (or all if none specified)
        organisms_to_check = organisms_to_process if selected_organisms is not None else [o for o in Organism if o != excluded]
        
        for organism in organisms_to_check:
            if organism != Organism.HUMAN and not self.protein_information.get(organism):
                # Pass selection callback if available
                selection_callback = getattr(self, '_ortholog_selection_callback', None)
                data = self.uniref_ortholog_finder.get_ortholog_ids(protein_id, organism, selection_callback=selection_callback)
                # If data is empty dict, selection is pending - don't set it yet
                if data:
                    self.protein_information[organism] = data
        
        return self._create_proteins(protein_name, protein_id, selected_organisms)
            
    def _create_proteins(self, protein_name, protein_id, selected_organisms=None):
        proteins = {}
        # Always include HUMAN
        organisms_to_create = [Organism.HUMAN]
        
        # Add selected organisms if provided, otherwise add all non-HUMAN organisms
        if selected_organisms is not None:
            organisms_to_create.extend(selected_organisms)
        else:
            organisms_to_create.extend([o for o in Organism if o != Organism.HUMAN])
        
        for organism in organisms_to_create:
            results = self.protein_information.get(organism)
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
    
    def set_ortholog_selection_callback(self, callback):
        """
        Set a callback function for ortholog selection when multiple options are found.
        
        Args:
            callback: Function that takes (organism_name, options_list) and returns selected accession.
                     options_list contains dicts with 'accession', 'source', and 'entry' keys.
        """
        self._ortholog_selection_callback = callback