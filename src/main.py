import streamlit as st
import csv
from pathlib import Path
from client.uniprot_client import UniProtClient
from models.organism import Organism, CustomOrganism
from models.entry import Entry
from models.image import Img
from driver import Driver

if 'cancel_process' not in st.session_state:
    st.session_state.cancel_process = False

def cancel():
    st.session_state.cancel_process = True

def _create_ortholog_selection_callback(protein_id):
    """
    Creates a callback function for ortholog selection that uses Streamlit UI.
    This function will be called when multiple orthologs are found.
    
    Args:
        protein_id: UniProt protein ID for creating unique keys
    """
    def select_ortholog(organism_name, options):
        """
        Callback function for selecting an ortholog when multiple are found.
        Stores selection request in session state for later UI display.
        
        Args:
            organism_name: Name of the organism
            options: List of dicts with 'accession', 'source', and 'entry' keys
            
        Returns:
            Selected accession ID, or None if user selection is needed
        """
        if len(options) == 1:
            return options[0]['accession']
        
        # Create a unique key for this selection
        selection_key = f"ortholog_selection_{organism_name}_{protein_id}"
        
        # Check if we already have a selection for this organism
        if selection_key in st.session_state:
            selected = st.session_state[selection_key].get('selected')
            if selected:
                # Verify the selected accession is still in options
                if any(opt['accession'] == selected for opt in options):
                    return selected
                # If selection is no longer valid, clear it
                st.session_state[selection_key]['selected'] = None
        
        # Store pending selection request
        st.session_state[selection_key] = {
            'options': options,
            'selected': None,
            'organism_name': organism_name,
            'pending': True
        }
        
        # Return None to indicate selection is needed
        return None
    
    return select_ortholog

def _handle_pending_ortholog_selections(protein_id):
    """
    Check for pending ortholog selections and display UI if needed.
    
    Returns:
        True if selections are pending and UI was shown, False otherwise
    """
    pending_selections = {}
    for key, value in st.session_state.items():
        if key.startswith('ortholog_selection_') and isinstance(value, dict) and value.get('pending'):
            pending_selections[key] = value
    
    if not pending_selections:
        return False
    
    st.markdown("### Ortholog Selection Required")
    st.info("Multiple orthologs were found for some organisms. Please select which one to use:")
    
    all_selected = True
    for selection_key, selection_data in pending_selections.items():
        organism_name = selection_data['organism_name']
        options = selection_data['options']
        
        # Create option labels
        option_labels = []
        for opt in options:
            source = opt.get('source', 'Unknown')
            accession = opt['accession']
            entry = opt.get('entry', {})
            if isinstance(entry, dict) and 'proteinDescription' in entry:
                try:
                    protein_name = entry['proteinDescription'].get('recommendedName', {}).get('fullName', {}).get('value', accession)
                except:
                    protein_name = accession
            else:
                protein_name = accession
            option_labels.append(f"{accession} ({source}) - {protein_name}")
        
        # Get current selection or default to first
        current_selection = selection_data.get('selected')
        default_index = 0
        if current_selection:
            try:
                default_index = next(i for i, opt in enumerate(options) if opt['accession'] == current_selection)
            except StopIteration:
                default_index = 0
        
        # Display selectbox
        selected_index = st.selectbox(
            f"Select ortholog for {organism_name}:",
            range(len(option_labels)),
            index=default_index,
            format_func=lambda x: option_labels[x],
            key=f"selectbox_{selection_key}"
        )
        
        if selected_index is not None:
            selected_accession = options[selected_index]['accession']
            st.session_state[selection_key]['selected'] = selected_accession
            st.session_state[selection_key]['pending'] = False
        else:
            all_selected = False
    
    return not all_selected

def _run_stepwise(protein_id, protein_name, full_name, selected_organisms, custom_organisms):
    """
    Run protein passport in steps so we can cancel mid-process.
    """
    driver = Driver(protein_id, custom_organisms=custom_organisms)
    
    # Set up ortholog selection callback for Streamlit UI
    selection_callback = _create_ortholog_selection_callback(protein_id)
    driver.set_ortholog_selection_callback(selection_callback)
    
    human = None
    orthologs = None

    st.info(f"Retrieving information for {protein_name}...")
    
    # Check for pending ortholog selections first
    if _handle_pending_ortholog_selections(protein_id):
        st.info("Please make your selections above and the process will continue.")
        return
    
    proteins = driver.drive(protein_name=protein_name, protein_id=protein_id, selected_organisms=selected_organisms)
    
    # Check again after drive() for any new pending selections
    if _handle_pending_ortholog_selections(protein_id):
        st.info("Please make your selections above and click 'Continue' to proceed.")
        if st.button("Continue Processing", key="continue_after_selection"):
            # Rerun with selections made
            st.rerun()
        return
    
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

    st.markdown("## Organism Selection")
    st.markdown("Select which organisms to use as orthologs (all selected by default):")
    
    # Get all organisms except HUMAN
    available_organisms = [org for org in Organism if org != Organism.HUMAN]
    
    # Initialize selected organisms in session state if not present
    if 'selected_organisms' not in st.session_state:
        st.session_state.selected_organisms = available_organisms.copy()
    
    # Initialize custom organisms in session state if not present
    if 'custom_organisms' not in st.session_state:
        st.session_state.custom_organisms = []
    
    # Create checkboxes for each predefined organism
    selected_organisms = []
    col1, col2 = st.columns(2)
    
    for i, organism in enumerate(available_organisms):
        col = col1 if i % 2 == 0 else col2
        with col:
            # Use organism.value[0] for display name (e.g., "Homo sapiens")
            organism_display_name = organism.value[0]
            is_selected = st.checkbox(
                organism_display_name,
                value=organism in st.session_state.selected_organisms,
                key=f"organism_{organism.name}"
            )
            if is_selected:
                selected_organisms.append(organism)
    
    # Custom organisms section
    st.markdown("### Add Custom Organisms")
    st.markdown("Enter scientific name and taxonomic ID to add custom organisms:")
    
    custom_scientific_name = st.text_input("Scientific Name (e.g., Canis lupus)", key="custom_scientific_name")
    custom_tax_id = st.text_input("Taxonomic ID (e.g., 9615)", key="custom_tax_id")
    
    if st.button("Add Custom Organism"):
        if custom_scientific_name and custom_tax_id:
            try:
                tax_id_int = int(custom_tax_id)
                custom_org = CustomOrganism(custom_scientific_name.strip(), tax_id_int)
                # Check if already exists
                if custom_org not in st.session_state.custom_organisms:
                    st.session_state.custom_organisms.append(custom_org)
                    st.success(f"Added {custom_scientific_name} (Tax ID: {tax_id_int})")
                else:
                    st.warning(f"{custom_scientific_name} (Tax ID: {tax_id_int}) already added")
            except ValueError:
                st.error("Taxonomic ID must be a valid integer")
        else:
            st.error("Please provide both scientific name and taxonomic ID")
    
    # Display and manage custom organisms
    if st.session_state.custom_organisms:
        st.markdown("**Custom Organisms:**")
        custom_selected = []
        organisms_to_remove = []
        
        for i, custom_org in enumerate(st.session_state.custom_organisms):
            col_custom1, col_custom2 = st.columns([4, 1])
            with col_custom1:
                display_text = f"{custom_org.value[0]} (Tax ID: {custom_org.tax_id})"
                is_custom_selected = st.checkbox(
                    display_text,
                    value=True,
                    key=f"custom_org_{i}"
                )
                if is_custom_selected:
                    custom_selected.append(custom_org)
            with col_custom2:
                if st.button("Remove", key=f"remove_custom_{i}"):
                    organisms_to_remove.append(i)
        
        # Remove organisms (in reverse order to maintain indices)
        if organisms_to_remove:
            for idx in sorted(organisms_to_remove, reverse=True):
                st.session_state.custom_organisms.pop(idx)
            st.rerun()
        
        # Add selected custom organisms to the main list
        selected_organisms.extend(custom_selected)
    
    # Update session state
    st.session_state.selected_organisms = selected_organisms

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
        # Get custom organisms that are selected
        selected_custom_orgs = [org for org in st.session_state.custom_organisms 
                                if org in selected_organisms]
        for protein_name, protein_id in proteins:
            _run_stepwise(protein_id, protein_name, full_name, selected_organisms, st.session_state.custom_organisms)

if __name__ == "__main__":
    main()
