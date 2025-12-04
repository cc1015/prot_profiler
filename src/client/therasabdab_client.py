import requests, sys, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import pandas as pd
from io import StringIO

class TherasabdabClient():
    """
    Represents Thera-SabDab client.

    Attributes:
        BASE_URL (str): Base url.
    """
    BASE_URL = "https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/therasabdab/search/"
    
    def fetch(self, protein_name, **kwargs) -> str:
        """
        Gets therasabdab data for a given protein.

        Args:
            protein_id (str): Protein of interest.
        
        Returns:
            dict: dataframe of thereasabdab data table.
        """
        params = {
            "theraformat": "All",
            "yearproposed": "All",
            "clintrial": "All",
            "stat": "All",
            "target": protein_name,
            "structures": "No",
        }

        r = requests.post(url=self.BASE_URL, data=params, verify=False)

        if not r.ok:
            r.raise_for_status()
            sys.exit()
        
        if r.status_code == 200 and r.text:
            tables = pd.read_html(StringIO(r.text))  
            return tables[0]
        else:
            return {}
