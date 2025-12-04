import streamlit as st
import csv
from pathlib import Path
from client.uniprot_client import UniProtClient
from models.organism import Organism
from models.entry import Entry
from models.image import Img
from driver import Driver

if 'cancel_process' not in st.session_state:
    st.session_state.cancel_process = False

def cancel():
    st.session_state.cancel_process = True

def _run_stepwise(protein_id, protein_name, full_name):
    """
    Run protein passport in steps so we can cancel mid-process.
    """
    driver = Driver(protein_id)
    human = None
    orthologs = None

    st.info(f"Retrieving information for {protein_name}...")
    proteins = driver.drive(protein_name=protein_name, protein_id=protein_id)
    if st.session_state.cancel_process:
        st.warning("Process cancelled during retrieval!")
        return
    human = proteins.get(Organism.HUMAN)
    orthologs = [protein for org, protein in proteins.items() if org != Organism.HUMAN]

    st.info("Annotating and aligning sequences...")
    human.annotate_align_seq_geneious(orthologs)
    if st.session_state.cancel_process:
        st.warning("Process cancelled during annotation/alignment!")
        return

    st.info("Performing structural alignment...")
    annotated_img_path = human.annotate_3d_structure()
    slide_1_img = Img(annotated_img_path, caption=human.pred_pdb_id)
    if st.session_state.cancel_process:
        st.warning("Process cancelled during 3D annotation!")
        return

    rmsd_map = human.structure_align(orthologs)
    slide_3_imgs = []
    for ortholog, (img_path, rmsd) in rmsd_map.items():
        slide_3_imgs.append(
            Img(img_path, caption=f"Human:{ortholog.organism.name}\nRMSD: {rmsd}Å")
        )
    if st.session_state.cancel_process:
        st.warning("Process cancelled during structure alignment!")
        return

    st.info("Retrieving STRING DB interactions...")
    slide_4_img = driver._get_string_db_interactions(protein_name, human.string_id)
    if st.session_state.cancel_process:
        st.warning("Process cancelled during STRING DB retrieval!")
        return

    st.info("Creating PowerPoint...")
    base_dir = Path(__file__).resolve().parent.parent  
    template_path = base_dir / "assets" / "template.pptx"
    entry = Entry(template_path=str(template_path), human=human, orthologs=orthologs, user_name=full_name)
    entry.populate_info_table_slide(slide_1_img)
    entry.populate_hu_seq_slide()
    entry.populate_str_align_slide(slide_3_imgs)
    entry.populate_string_db_slide(slide_4_img)

    st.success("Process completed successfully!")

def main():
    st.title("Protein Passport Generator")

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    full_name = f"{first_name} {last_name}"

    st.markdown("## Input Options")
    input_option = st.radio("Choose input method:", ["Single Entry", "CSV Upload"])

    proteins = []

    if input_option == "CSV Upload":
        csv_file = st.file_uploader("Upload CSV with columns: protein_name, protein_id", type="csv")
        if csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if len(row) >= 2:
                    proteins.append((row[0].strip(), row[1].strip()))
    else:
        protein_name = st.text_input("Protein Name")
        protein_id = st.text_input("UniProt Accession")
        if protein_name and protein_id:
            proteins.append((protein_name.strip(), protein_id.strip()))

    st.button("Cancel", on_click=cancel)

    if st.button("Create"):
        st.session_state.cancel_process = False  
        for protein_name, protein_id in proteins:
            _run_stepwise(protein_id, protein_name, full_name)

if __name__ == "__main__":
    main()
