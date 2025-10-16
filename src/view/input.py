import streamlit as st
import pandas as pd

class Input:
    def main_input(self):
        st.title("Protein Passport Generator")
        with st.form("input"):
            name = st.text_input("Full Name")
            
            st.header("Single Upload")
            protein_name = st.text_input("Target Name")
            protein_id = st.text_input("Target UniProt Accession")
            
            st.header("Batch Upload")
            st.write("Batch CSV Format")
            example_header = pd.DataFrame([
                ["Protein Name 1", "Protein ID 1"],
                ["Protein Name 2", "Protein ID 2"],
                ["Protein Name 3", "Protein ID 3"],
                ["...", "..."]
            ])
            st.table(example_header)

            csv = st.file_uploader("Choose a .csv file")
            
            st.header("Orthologs")
            st.checkbox("Mus musculus", value=True)
            st.checkbox("Macaca fascicularis", value=True)
            st.checkbox("Vicugna pacos", value=True)
            st.checkbox("Gallus gallus", value=True)
            st.checkbox("Oryctolagus cuniculus", value=True)
            st.checkbox("Lama glama", value=True)
            
            st.header("Output Options")
            st.radio("Select Output Option",
                     ["Generate Powerpoint", "Generate Sequence Homologies ONLY"])
            
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                return {
                    "name": name,
                    "protein_name": protein_name,
                    "protein_id": protein_id,
                    "csv": csv,
                    }
    