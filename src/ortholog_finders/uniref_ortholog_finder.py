from client.uniprot_client import UniProtClient
from models.organism import Organism, CustomOrganism

class UniRefOrthologFinder():
    uniprot_client = UniProtClient()
    
    def get_ortholog_ids(self, protein_id, organism, selection_callback=None):
        """
        Get ortholog IDs for a given organism.
        
        Args:
            protein_id: UniProt protein ID
            organism: Organism enum or CustomOrganism instance
            selection_callback: Optional callback function for user selection when multiple orthologs are found.
                              Should accept (organism_name, options_list) and return selected accession.
                              If None, auto-selects first option.
        """
        human_data =  self.uniprot_client.get_entry(protein_id)
        uniref_data = self.uniprot_client.get_entry(protein_id, ref=True)
    
        protein_name = human_data['genes'][0]['geneName']['value']
        rec_name=human_data['proteinDescription']['recommendedName']['fullName']['value']

        orthologs = [organism]
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
                        # Multiple options found - need user selection
                        options = []
                        # Add UniRef accessions
                        for acc in result['accessions']:
                            options.append({'accession': acc, 'source': 'UniRef', 'entry': uniref_r if acc == match_id else None})
                        # Add search results
                        for entry in search_r['results']:
                            if entry['primaryAccession'] not in result['accessions']:
                                options.append({'accession': entry['primaryAccession'], 'source': 'UniProtKB Search', 'entry': entry})
                        
                        if len(options) > 1 and selection_callback:
                            chosen_ortholog = selection_callback(match.value[0], options)
                            if chosen_ortholog:
                                data = self.uniprot_client.get_entry(chosen_ortholog, kb=True)
                            else:
                                # Selection pending - return empty dict to indicate selection needed
                                return {}
                        else:
                            # Auto-select first option if no callback or only one option
                            chosen_ortholog = options[0]['accession'] if options else None
                            if chosen_ortholog:
                                data = self.uniprot_client.get_entry(chosen_ortholog, kb=True)
                    orthologs.remove(match)
                if not orthologs: break
        
        for org in orthologs:
            r = self.uniprot_client.get_entry(protein_id=rec_name, gene=protein_name, organism=org.value[1], kb=True, search=True)
            if r['results']:
                if len(r['results']) > 1 and selection_callback:
                    # Multiple search results - need user selection
                    options = [{'accession': entry['primaryAccession'], 'source': 'UniProtKB Search', 'entry': entry} 
                              for entry in r['results']]
                    chosen_ortholog = selection_callback(org.value[0], options)
                    if chosen_ortholog:
                        chosen_entry = next((opt['entry'] for opt in options if opt['accession'] == chosen_ortholog), None)
                        data = chosen_entry if chosen_entry else r['results'][0]
                    else:
                        # Selection pending - return empty dict to indicate selection needed
                        return {}
                else:
                    data = r['results'][0]
           
        return data