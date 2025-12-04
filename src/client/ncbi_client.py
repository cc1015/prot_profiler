import requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup

class NCBIClient():
    """
    Represents NCBI client.
    """
    
    def get_orthologs(self, gene_id, taxon_list):
        """
        Gets taxon_list orthologs of given gene_id.
        """
        url = f"https://api.ncbi.nlm.nih.gov/datasets/v2/gene/id/{gene_id}/orthologs"
        params = {
            "taxon_filter": taxon_list
        }
        
        r = requests.get(url, params=params)
        
        if not r.ok:
            return {}
        
        data = r.json()
        return data

    def get_protein_reference_id(self, gene_id) -> str:
        """
        Gets protein ortholog information.
        """
        url = f"https://www.ncbi.nlm.nih.gov/gene/{gene_id}"
        r = requests.get(url)
        
        if not r.ok:
            return ""
        
        soup = BeautifulSoup(r.text, "html.parser")
        section = soup.find("section", class_="rprt-section gene-reference-sequences")
        if not section:
            return ""

        mrna_sections = section.find_all("h4", id=lambda x: x and x.startswith("mrnaandproteins"))
        if not mrna_sections:
            return ""
        
        li = mrna_sections[0].find_next("ol").find_all("li")
        
        for item in li:
            if not item:
                return ""
        
            uniprot_section = item.find("dt", string=lambda s: s and "UniProtKB/Swiss-Prot" in s)
            if uniprot_section:
                uniprot_link = uniprot_section.find_next("a")
                if uniprot_link:
                    return ('uniprot', uniprot_link.get_text(strip=True))

            uniprot_section = item.find("dt", string=lambda s: s and "UniProtKB/TrEMBL" in s)
            if uniprot_section:
                uniprot_link = uniprot_section.find_next("a")
                if uniprot_link:
                    return ('uniprot', uniprot_link.get_text(strip=True))

        p_tag = li[0].find("p")
        if p_tag and "→" in p_tag.text:
            try:
                refseq_id = p_tag.text.split("→")[1].strip().split()[0]
                return ('ncbi', refseq_id)
            except IndexError:
                pass

        return ""

    def get_entry(self, protein_id):
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        
        params = {
            "db": "protein",
            "id": protein_id,
            "rettype": "fasta",
            "retmode": "text"
        }
        
        r = requests.get(url, params=params)
        return ('ncbi', r.text)