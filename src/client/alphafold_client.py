import requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AlphaFoldClient:
    """
    Represents AlphaFold client.

    Attributes:
        BASE_URL (str): Base url.
    """
    BASE_URL = "https://alphafold.ebi.ac.uk"

    def get_af_pdb(self, protein_id: str, **kwargs) -> dict:
        """
        Gets AlphaFold PDB file of given protein.

        Args:
            protein_id (str): Protein of interest.
        
        Returns:
            dict: File name and content
        """
        url = f"{self.BASE_URL}/api/prediction/{protein_id}"
            
        r = requests.get(url, verify=False)

        if not r.ok:
            return {}

        pdb_list = r.json()
        
        for pdb in pdb_list:
            if pdb['uniprotAccession'] == protein_id:
                response_dict = pdb
        
        if response_dict is None:
            response_dict = pdb_list[0]
                
        pdb_url = response_dict['pdbUrl']

        pdb_file_name = pdb_url.rsplit("/",1)[-1]

        pdb_r = requests.get(pdb_url, verify=False)

        return {'file_name': pdb_file_name,
                'content': pdb_r.content}
