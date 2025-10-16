import requests, sys, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UniProtClient():
    """
    Represents UniProt client.

    Attributes:
        BASE_URL (str): Base url.
    """
    BASE_URL = "https://rest.uniprot.org"

    def get_entry(self, protein_id) -> dict:
        """
        Gets UniProt information.

        Args:
            protein_id (str): Protein of interest.
        
        Returns:
            dict: Uniprot data.
        """
        params = {
            "fields": [
                "accession",
                "protein_name",
                "organism_name",
                "sequence",
                "mass",
                "cc_subcellular_location",
                "xref_pdb",
                "cc_function",
                "cc_tissue_specificity",
                "xref_string",
                "gene_names"
                ]
            }
        
        headers = {
            "accept": "application/json"
            }
        
        path = protein_id
        
        url = '/'.join([self.BASE_URL, "uniprotkb", path])
        
        r = requests.get(url, headers=headers, params=params, verify=False)
        
        if not r.ok:
            return {}
        
        data = r.json()
        return data
    
    def get_fasta(self, protein_id):
        url = '/'.join([self.BASE_URL, "uniprotkb", protein_id + ".fasta"])
        r = requests.get(url, verify=False)
        return r.text 
    
    def get_annotations(self, protein_id):
        url = f"https://rest.uniprot.org/uniprotkb/{protein_id}.json?fields=ft_var_seq%2Cft_variant%2Cft_non_cons%2Cft_non_std%2Cft_non_ter%2Cft_conflict%2Cft_unsure%2Cft_act_site%2Cft_binding%2Cft_dna_bind%2Cft_site%2Cft_mutagen%2Cft_intramem%2Cft_topo_dom%2Cft_transmem%2Cft_chain%2Cft_crosslnk%2Cft_disulfid%2Cft_carbohyd%2Cft_init_met%2Cft_lipid%2Cft_mod_res%2Cft_peptide%2Cft_propep%2Cft_signal%2Cft_transit%2Cft_strand%2Cft_helix%2Cft_turn%2Cft_coiled%2Cft_compbias%2Cft_domain%2Cft_motif%2Cft_region%2Cft_repeat%2Cft_zn_fing"
        r = requests.get(url, verify=False)
        return r.json()
            