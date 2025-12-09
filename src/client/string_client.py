import requests, sys, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from time import sleep
from pathlib import Path
from utils.file_utils import ensure_directory, safe_open_write

class StringClient():
    """
    Represents STRING client.

    Attributes:
        BASE_URL (str): Base url.
    """
    BASE_URL = "https://string-db.org/api"
    
    def fetch(self, protein_name, **kwargs) -> str:
        """
        Gets STRING network image file of given protein.

        Args:
            protein_id (str): Protein of interest.
        
        Returns:
            str: Image file path.
        """
        output_format = "image"
        method = "network"
        params = {
            "identifiers" : kwargs.get('string_id'), 
            "species" : 9606, 
            "network_flavor": "confidence",
            "network_type": "physical",
            "add_color_nodes": 20
            }

        url = "/".join([self.BASE_URL, output_format, method]) 
        r = requests.post(url, data=params, verify=False)

        if not r.ok:
            r.raise_for_status()
            sys.exit()

        output_dir = Path(__file__).parent.parent.parent
        ensure_directory(output_dir)

        file_name = output_dir / f"output_{protein_name}" / "string_network.png"
        ensure_directory(file_name.parent)

        with safe_open_write(file_name, 'wb') as fh:
            fh.write(r.content)
        
        sleep(1)
        
        return str(file_name)
