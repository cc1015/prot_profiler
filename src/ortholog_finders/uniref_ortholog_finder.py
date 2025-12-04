from client.uniprot_client import UniProtClient
from models.organism import Organism

class UniRefOrthologFinder():
    uniprot_client = UniProtClient()
    
    def get_ortholog_ids(self, protein_id, taxon_id):
        human_data =  self.uniprot_client.get_entry(protein_id)
        uniref_data = self.uniprot_client.get_entry(protein_id, ref=True)
    
        protein_name = human_data['genes'][0]['geneName']['value']
        rec_name=human_data['proteinDescription']['recommendedName']['fullName']['value']

        orthologs = [taxon_id]
        data = {}
        
        if uniref_data.get('results'):
            for result in uniref_data['results']:
                match = next((o for o in orthologs if result['organismTaxId'] == o.value[1] and result['proteinName'] == rec_name), None)
                if match:
                    match_id = result['accessions'][0]
                    uniref_r = self.uniprot_client.get_entry(protein_id=match_id, kb=True)
                    search_r = self.uniprot_client.get_entry(protein_id=rec_name, gene=protein_name, organism=match.value[1], kb=True, search=True)
                    if uniref_r['primaryAccession'] == search_r['results'][0]['primaryAccession']:
                        data = uniref_r
                    else:
                        chosen_ortholog = self._choose_ortholog_selection(organism_str=match.name, uniref_accessions=result['accessions'], search=search_r['results'])
                        data = self.uniprot_client.get_entry(chosen_ortholog, kb=True)
                    orthologs.remove(match)
                if not orthologs: break
        
        for organism in orthologs:
            r = self.uniprot_client.get_entry(protein_id=rec_name, gene=protein_name, organism=organism.value[1], kb=True, search=True)
            if r['results']:
                data = r['results'][0]
           
        return data