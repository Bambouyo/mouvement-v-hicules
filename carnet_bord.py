import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AutoParc Manager", layout="wide", page_icon="🚗")

# --- CHARGEMENT / INITIALISATION DES DONNÉES ---
def load_data(filename, columns):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=columns)

# Fichiers de stockage
vehicles_file = "vehicules.csv"
maintenance_file = "maintenance.csv"
rotations_file = "rotations.csv"

# Initialisation des DataFrames
df_vehicles = load_data(vehicles_file, ["Immatriculation", "Modèle", "Statut", "Kilométrage"])
df_maint = load_data(maintenance_file, ["Immatriculation", "Date", "Type", "Coût", "Commentaire"])
df_rotations = load_data(rotations_file, ["Immatriculation", "Chauffeur", "Départ", "Retour", "Destination"])

# --- BARRE LATÉRALE ---
st.sidebar.title("🚗 AutoParc v1.0")
menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Gestion Flotte", "Maintenance", "Rotations & Planning"])

# --- SECTION 1 : TABLEAU DE BORD ---
if menu == "Tableau de Bord":
    st.title("📊 État du Parc en Temps Réel")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Véhicules", len(df_vehicles))
    col2.metric("En Service", len(df_vehicles[df_vehicles['Statut'] == "Disponible"]))
    col3.metric("En Maintenance", len(df_vehicles[df_vehicles['Statut'] == "Atelier"]))

    st.subheader("Aperçu de la Flotte")
    st.dataframe(df_vehicles, use_container_width=True)

# --- SECTION 2 : GESTION DE LA FLOTTE ---
elif menu == "Gestion Flotte":
    st.title("🚜 Gestion des Véhicules")
    
    with st.expander("➕ Ajouter un nouveau véhicule"):
        with st.form("add_vehicle"):
            imm = st.text_input("Immatriculation")
            model = st.text_input("Modèle (ex: Toyota Hilux)")
            km = st.number_input("Kilométrage Initial", min_value=0)
            submitted = st.form_submit_button("Enregistrer")
            
            if submitted and imm:
                new_v = pd.DataFrame([[imm, model, "Disponible", km]], columns=df_vehicles.columns)
                df_vehicles = pd.concat([df_vehicles, new_v], ignore_index=True)
                df_vehicles.to_csv(vehicles_file, index=False)
                st.success(f"Véhicule {imm} ajouté !")
                st.rerun()

    st.write("### Liste des véhicules")
    st.table(df_vehicles)

# --- SECTION 3 : MAINTENANCE ---
elif menu == "Maintenance":
    st.title("🛠 Suivi de la Maintenance")
    
    tab1, tab2 = st.tabs(["Enregistrer une intervention", "Historique"])
    
    with tab1:
        if not df_vehicles.empty:
            with st.form("maint_form"):
                v_choice = st.selectbox("Véhicule", df_vehicles["Immatriculation"])
                m_type = st.selectbox("Type d'intervention", ["Vidange", "Pneumatiques", "Freins", "Révision Générale", "Réparation"])
                date_m = st.date_input("Date", date.today())
                cost = st.number_input("Coût (FCFA)", min_value=0)
                note = st.text_area("Observations")
                
                if st.form_submit_button("Valider l'intervention"):
                    new_m = pd.DataFrame([[v_choice, date_m, m_type, cost, note]], columns=df_maint.columns)
                    pd.concat([df_maint, new_m], ignore_index=True).to_csv(maintenance_file, index=False)
                    # Mise à jour du statut
                    df_vehicles.loc[df_vehicles['Immatriculation'] == v_choice, 'Statut'] = "Atelier"
                    df_vehicles.to_csv(vehicles_file, index=False)
                    st.warning(f"Véhicule {v_choice} marqué comme 'En Atelier'")
        else:
            st.info("Ajoutez d'abord des véhicules.")

    with tab2:
        st.dataframe(df_maint, use_container_width=True)

# --- SECTION 4 : ROTATIONS ---
elif menu == "Rotations & Planning":
    st.title("📅 Gestion des Rotations")
    
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("Nouvelle Rotation")
        available_v = df_vehicles[df_vehicles['Statut'] == "Disponible"]["Immatriculation"]
        
        if not available_v.empty:
            with st.form("rotation_form"):
                v_rot = st.selectbox("Sélectionner un véhicule", available_v)
                driver = st.text_input("Nom du Chauffeur")
                dest = st.text_input("Destination")
                start_d = st.date_input("Date de départ")
                end_d = st.date_input("Date de retour prévue")
                
                if st.form_submit_button("Assigner la rotation"):
                    new_r = pd.DataFrame([[v_rot, driver, start_d, end_d, dest]], columns=df_rotations.columns)
                    pd.concat([df_rotations, new_r], ignore_index=True).to_csv(rotations_file, index=False)
                    
                    # Passage en statut "En Mission"
                    df_vehicles.loc[df_vehicles['Immatriculation'] == v_rot, 'Statut'] = "En Mission"
                    df_vehicles.to_csv(vehicles_file, index=False)
                    st.success(f"Mission confirmée pour {v_rot}")
                    st.rerun()
        else:
            st.error("Aucun véhicule disponible pour une rotation.")

    with col_b:
        st.subheader("Missions en cours")
        st.dataframe(df_rotations, use_container_width=True)
