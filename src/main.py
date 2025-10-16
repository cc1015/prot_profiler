import argparse
import csv
from pathlib import Path
from client.uniprot_client import UniProtClient
from models.organism import Organism
from models.entry import Entry
from models.image import Img
from driver import Driver
from view.input import Input

def _confirm_ortholog_selection(orthologs):
    while True:
        prompt = f"Using the following orthologs to create Protein Passport:\n"
    
        for organism, data in orthologs.items():
            prompt += f"{organism.name}: {data['primaryAccession']}\n"
    
        prompt += "Press \'y\' if you would like to continue with these orthologs. If incorrect orthologs are present, press \'c\' to enter orthologs manually: "
    
        response = input(prompt).strip().lower()
    
        if response == 'y':
            return orthologs
        elif response == 'c':
            orthologs = _custom_orthologs()
        
def _custom_orthologs():
    uniprot_data = {o: None for o in Organism}
    for organism in Organism:
        protein_id = input(f"Please enter desired {organism.name} UniProt Accession (enter nothing for no ortholog): ").strip()
        uniprot_client = UniProtClient()
        data =  uniprot_client.fetch(protein_id, kb=True)
        if data:
            uniprot_data[organism] = data
    return uniprot_data
        

def _run(protein_id, protein_name, full_name):
    driver = Driver()
    # print(f"Retrieving information for {protein_name}...")
    uniprot_data = driver.uniprot_query(protein_name=protein_name, protein_id=protein_id)
    
    #confirmed_orthologs = _confirm_ortholog_selection(uniprot_data)
    
    proteins = driver.create_proteins(uniprot_data=uniprot_data, protein_name=protein_name)
    human = proteins.get(Organism.HUMAN)
    orthologs = [protein for organism, protein in proteins.items() if organism != Organism.HUMAN]

    # print("Annotating and aligning sequences...")
    human.annotate_align_seq_geneious(orthologs)
    # print("Completed")

    # print("Performing structural alignment...")
    annotated_img_path = human.annotate_3d_structure()
    slide_1_img = Img(annotated_img_path, caption=human.pred_pdb_id)

    rmsd_map = human.structure_align(orthologs)
    # print(rmsd_map)
    slide_3_imgs = []
    for ortholog, (img_path, rmsd) in rmsd_map.items():
        slide_3_imgs.append(Img(img_path, caption="Human:" + ortholog.organism.name.capitalize() + "\nRMSD: " + str(rmsd) + "Å"))
    
    
    slide_4_img = driver._get_string_db_interactions(protein_name, human.string_id)

    
    # print("Creating powerpoint...")
    template_path = Path(__file__).parent.parent / "assets" / "template.pptx"
    entry = Entry(template_path=template_path, human=human, orthologs=orthologs, user_name=full_name)
    entry.populate_info_table_slide(slide_1_img)
    entry.populate_hu_seq_slide()
    entry.populate_str_align_slide(slide_3_imgs)
    entry.populate_string_db_slide(slide_4_img)
    

    
def main():
    '''
    parser = argparse.ArgumentParser(description="Protein passport automation")
    
    parser.add_argument("first_name", help="Your first name")
    parser.add_argument("last_name", help="Your last name")

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--csv",
        help="Path to CSV file with columns: protein_name, protein_id"
    )

    group.add_argument(
        "--manual",
        nargs=2,
        metavar=("protein_name", "protein_id"),
        help="Provide protein_name and protein_id directly"
    )

    args = parser.parse_args()

    proteins = []

    if args.csv:
        with open(args.csv, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2:  
                    proteins.append((row[0].strip(), row[1].strip()))
    elif args.manual:
        protein_name, protein_id = args.manual
        proteins.append((protein_name, protein_id))

    for protein_name, protein_id in proteins:
        _run(protein_id, protein_name, args.first_name, args.last_name)
    '''
    view = Input()
    input = view.main_input()
    
    proteins = []
    
    if input.get(csv):
        with open(input.get(csv), newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2:
                    proteins.append((row[0].strip(), row[1].strip()))
    else:
        proteins.append(input.get(protein_name), input.get(protein_id))
    
    for protein_name, protein_id in proteins:
        output_data = _run(protein_id, protein_name, input.name)

if __name__ == "__main__":
    main()