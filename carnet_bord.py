"""
Carnet de Bord - Centre National des Archives (CNA)
Application de suivi des déplacements de véhicules

Installation requise:
pip install streamlit>=1.28.0 pandas

Lancement:
streamlit run carnet_de_bord.py

Mot de passe par défaut: cna2024
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# Configuration de la page
st.set_page_config(
    page_title="Carnet de Bord - CNA",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé pour améliorer l'apparence
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #000000 0%, #ff8c00 40%, #32cd32 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        min-height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .header-content {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        flex-wrap: wrap;
    }
    
    .cna-logo {
        background: linear-gradient(135deg, #f39c12, #e67e22);
        color: white;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.4rem;
        margin-right: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        flex-shrink: 0;
    }
    
    .header-text {
        text-align: left;
        flex-grow: 1;
    }
    
    .header-text h1 {
        font-size: 2rem;
        margin-bottom: 5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .header-text p {
        font-size: 1rem;
        opacity: 0.9;
        margin-bottom: 3px;
    }
    
    .header-text small {
        font-size: 0.8rem;
        opacity: 0.8;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin-bottom: 1rem;
    }
    
    .vehicle-plate {
        background: #3498db;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .trip-type-prof {
        background: #e8f5e8;
        color: #27ae60;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .trip-type-private {
        background: #fff3cd;
        color: #856404;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    .login-logo {
        background: linear-gradient(135deg, #f39c12, #e67e22);
        color: white;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.5rem;
        margin: 0 auto 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# Configuration des véhicules
VEHICLES = {
    'ford': {
        'name': 'Ford (Fourgon)',
        'plate': 'AA 696 ET',
        'toll_balance': 30000
    },
    'renault': {
        'name': 'Renault Logan (Berline)',
        'plate': 'DK 0953 BK',
        'toll_balance': 30000
    }
}

# Configuration de l'authentification
DEFAULT_PASSWORD = 'cna2024'

# Initialisation du state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'trips' not in st.session_state:
        st.session_state.trips = []
    if 'toll_usage' not in st.session_state:
        st.session_state.toll_usage = {'ford': 0, 'renault': 0}

# Page de connexion
def login_page():
    st.markdown("""
    <div class="login-container">
        <div class="login-logo">CNA</div>
        <h1>🔐 Connexion</h1>
        <p>Centre National des Archives<br>Carnet de Bord - Suivi de Véhicules</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        password = st.text_input("Mot de passe", type="password", placeholder="Saisissez votre mot de passe")
        submitted = st.form_submit_button("Se connecter", use_container_width=True)
        
        if submitted:
            if password == DEFAULT_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect. Veuillez réessayer.")

# Header de l'application
def show_header():
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <div class="cna-logo">CNA</div>
            <div class="header-text">
                <h1>🚗 Carnet de Bord</h1>
                <p>Suivi et gestion des déplacements de véhicules</p>
                <small>Centre National des Archives</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Bouton de déconnexion
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        if st.button("🚪 Déconnexion", type="secondary"):
            st.session_state.authenticated = False
            st.rerun()

# Fonction pour ajouter un nouveau déplacement
def add_trip_page():
    st.header("Ajouter un nouveau déplacement")
    
    with st.form("trip_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vehicle = st.selectbox("Véhicule *", 
                                 options=['', 'ford', 'renault'],
                                 format_func=lambda x: '' if x == '' else VEHICLES[x]['name'])
            
            driver_name = st.text_input("Prénom et Nom de l'utilisateur *")
            
            departure_date_col1, departure_time_col1 = st.columns(2)
            with departure_date_col1:
                departure_date_part = st.date_input("Date de sortie *", value=datetime.now().date())
            with departure_time_col1:
                departure_time_part = st.time_input("Heure de sortie *", value=datetime.now().time())
            departure_date = datetime.combine(departure_date_part, departure_time_part)
        
        with col2:
            driver_registration = st.text_input("Matricule de l'utilisateur *")
            
            trip_type = st.selectbox("Type de sortie *",
                                   options=['', 'professional', 'private'],
                                   format_func=lambda x: {'': '', 'professional': 'Professionnelle', 'private': 'Privée'}[x])
            
            return_date_col1, return_time_col1 = st.columns(2)
            with return_date_col1:
                return_date_part = st.date_input("Date de retour *", value=(datetime.now() + timedelta(hours=2)).date())
            with return_time_col1:
                return_time_part = st.time_input("Heure de retour *", value=(datetime.now() + timedelta(hours=2)).time())
            return_date = datetime.combine(return_date_part, return_time_part)
        
        with col3:
            initial_km = st.number_input("Kilométrage initial *", min_value=0, step=1, key="initial_km")
            
            final_km = st.number_input("Kilométrage final *", min_value=0, step=1, key="final_km")
            
            # Calcul automatique de la distance avec mise à jour en temps réel
            if initial_km and final_km and final_km >= initial_km:
                distance_traveled = final_km - initial_km
                st.success(f"✅ Kilomètres parcourus : **{distance_traveled:,} km**")
            elif initial_km and final_km and final_km < initial_km:
                st.error("❌ Le kilométrage final ne peut pas être inférieur au kilométrage initial")
                distance_traveled = 0
            else:
                st.info("ℹ️ Kilomètres parcourus : En attente des valeurs...")
                distance_traveled = 0
        
        trip_purpose = st.text_input("Objet du déplacement *")
        itinerary = st.text_area("Itinéraire", placeholder="Décrivez l'itinéraire suivi...")
        
        # Gestion du péage
        used_toll = st.checkbox("Passage par le péage")
        toll_amount = 0
        toll_direction = 'aller'
        
        if used_toll:
            col_toll1, col_toll2 = st.columns(2)
            with col_toll1:
                toll_amount = st.number_input("Montant payé au péage (F CFA) *", min_value=0, step=100)
            with col_toll2:
                toll_direction = st.selectbox("Direction",
                                            options=['aller', 'retour', 'aller-retour'],
                                            format_func=lambda x: {'aller': 'Aller seulement', 
                                                                  'retour': 'Retour seulement', 
                                                                  'aller-retour': 'Aller-Retour'}[x])
        
        # Affichage des informations du véhicule
        if vehicle:
            vehicle_info = VEHICLES[vehicle]
            st.info(f"**Véhicule sélectionné:** {vehicle_info['name']} - Plaque: {vehicle_info['plate']}")
        
        submitted = st.form_submit_button("Enregistrer le déplacement", use_container_width=True)
        
        if submitted:
            # Validation
            if not all([vehicle, driver_name, driver_registration, trip_type, trip_purpose]):
                st.error("Veuillez remplir tous les champs obligatoires (*)")
                return
            
            if return_date < departure_date:
                st.error("La date de retour ne peut pas être antérieure à la date de sortie.")
                return
            
            if final_km < initial_km:
                st.error("Le kilométrage final ne peut pas être inférieur au kilométrage initial.")
                return
            
            if used_toll and toll_amount <= 0:
                st.error("Veuillez saisir le montant du péage si vous avez coché 'Passage par le péage'.")
                return
            
            # Vérifier le solde de la carte de péage
            if used_toll and toll_amount > 0:
                current_toll_usage = st.session_state.toll_usage[vehicle]
                remaining_balance = 30000 - current_toll_usage
                
                if toll_amount > remaining_balance:
                    st.error(f"Solde insuffisant sur la carte de péage ! Solde restant : {remaining_balance:,} F CFA")
                    return
            
            # Créer le nouveau déplacement
            new_trip = {
                'id': len(st.session_state.trips) + 1,
                'vehicle': vehicle,
                'vehicle_name': VEHICLES[vehicle]['name'],
                'vehicle_plate': VEHICLES[vehicle]['plate'],
                'driver_name': driver_name,
                'driver_registration': driver_registration,
                'departure_date': departure_date,
                'return_date': return_date,
                'initial_km': initial_km,
                'final_km': final_km,
                'distance_traveled': distance_traveled,
                'trip_type': trip_type,
                'trip_purpose': trip_purpose,
                'itinerary': itinerary,
                'used_toll': used_toll,
                'toll_amount': toll_amount,
                'toll_direction': toll_direction
            }
            
            # Ajouter le déplacement
            st.session_state.trips.append(new_trip)
            
            # Mettre à jour l'usage du péage
            if used_toll and toll_amount > 0:
                st.session_state.toll_usage[vehicle] += toll_amount
            
            # Message de succès
            success_message = "Déplacement enregistré avec succès !"
            if used_toll and toll_amount > 0:
                remaining_balance = 30000 - st.session_state.toll_usage[vehicle]
                success_message += f"\n💳 Montant déduit de la carte : {toll_amount:,} F CFA"
                success_message += f"\n💰 Solde restant : {remaining_balance:,} F CFA"
            
            st.success(success_message)

# Tableau de bord
def dashboard_page():
    st.header("Tableau de Bord")
    
    # Statistiques par véhicule
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculs des statistiques
    ford_trips = [trip for trip in st.session_state.trips if trip['vehicle'] == 'ford']
    renault_trips = [trip for trip in st.session_state.trips if trip['vehicle'] == 'renault']
    
    ford_km = sum(trip['distance_traveled'] for trip in ford_trips)
    renault_km = sum(trip['distance_traveled'] for trip in renault_trips)
    
    ford_toll_used = st.session_state.toll_usage['ford']
    renault_toll_used = st.session_state.toll_usage['renault']
    
    ford_toll_balance = 30000 - ford_toll_used
    renault_toll_balance = 30000 - renault_toll_used
    
    ford_toll_rate = (ford_toll_used / 30000) * 100
    renault_toll_rate = (renault_toll_used / 30000) * 100
    
    with col1:
        st.metric("🚐 Ford (Fourgon) - Déplacements", len(ford_trips))
        st.metric("Kilomètres parcourus", f"{ford_km:,}")
    
    with col2:
        st.metric("🚗 Renault Logan - Déplacements", len(renault_trips))
        st.metric("Kilomètres parcourus", f"{renault_km:,}")
    
    with col3:
        st.metric("🏷️ Carte Péage Ford - Solde restant", f"{ford_toll_balance:,} F CFA")
        st.metric("Montant utilisé", f"{ford_toll_used:,} F CFA")
        st.metric("Taux d'utilisation", f"{ford_toll_rate:.1f}%")
    
    with col4:
        st.metric("🏷️ Carte Péage Renault - Solde restant", f"{renault_toll_balance:,} F CFA")
        st.metric("Montant utilisé", f"{renault_toll_used:,} F CFA")
        st.metric("Taux d'utilisation", f"{renault_toll_rate:.1f}%")
    
    # Alertes pour soldes faibles
    if ford_toll_balance < 5000:
        st.warning(f"⚠️ Solde faible sur la carte de péage Ford : {ford_toll_balance:,} F CFA")
    
    if renault_toll_balance < 5000:
        st.warning(f"⚠️ Solde faible sur la carte de péage Renault : {renault_toll_balance:,} F CFA")
    
    # Statistiques par utilisateur
    st.subheader("Statistiques par utilisateur")
    
    if st.session_state.trips:
        driver_stats = {}
        for trip in st.session_state.trips:
            driver_name = trip['driver_name']
            if driver_name not in driver_stats:
                driver_stats[driver_name] = {
                    'registration': trip['driver_registration'],
                    'trips': 0,
                    'total_km': 0
                }
            driver_stats[driver_name]['trips'] += 1
            driver_stats[driver_name]['total_km'] += trip['distance_traveled']
        
        # Affichage en colonnes
        cols = st.columns(min(len(driver_stats), 4))
        for i, (driver_name, stats) in enumerate(driver_stats.items()):
            with cols[i % 4]:
                st.metric(f"👤 {driver_name}", f"{stats['trips']} déplacements")
                st.caption(f"Matricule: {stats['registration']}")
                st.caption(f"Kilomètres: {stats['total_km']:,}")
    else:
        st.info("Aucun déplacement enregistré pour le moment.")
    
    # Export CSV
    if st.session_state.trips:
        if st.button("📊 Exporter en CSV", type="primary"):
            df = pd.DataFrame(st.session_state.trips)
            df['departure_date'] = pd.to_datetime(df['departure_date']).dt.strftime('%d/%m/%Y %H:%M')
            df['return_date'] = pd.to_datetime(df['return_date']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Renommer les colonnes pour l'export
            df_export = df.rename(columns={
                'departure_date': 'Date de sortie',
                'return_date': 'Date de retour',
                'vehicle_name': 'Véhicule',
                'vehicle_plate': 'Plaque',
                'driver_name': 'Utilisateur',
                'driver_registration': 'Matricule',
                'trip_type': 'Type de sortie',
                'trip_purpose': 'Objet du déplacement',
                'itinerary': 'Itinéraire',
                'initial_km': 'Km initial',
                'final_km': 'Km final',
                'distance_traveled': 'Distance parcourue',
                'used_toll': 'Péage utilisé',
                'toll_amount': 'Montant péage',
                'toll_direction': 'Direction péage'
            })
            
            # Sélectionner les colonnes pour l'export
            export_columns = [
                'Date de sortie', 'Date de retour', 'Véhicule', 'Plaque',
                'Utilisateur', 'Matricule', 'Type de sortie', 'Objet du déplacement',
                'Itinéraire', 'Km initial', 'Km final', 'Distance parcourue',
                'Péage utilisé', 'Montant péage', 'Direction péage'
            ]
            
            csv = df_export[export_columns].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="Télécharger le fichier CSV",
                data=csv,
                file_name=f"carnet_de_bord_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# Historique des déplacements
def history_page():
    st.header("Historique des déplacements")
    
    if not st.session_state.trips:
        st.info("Aucun déplacement enregistré pour le moment.")
        return
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_vehicle = st.selectbox("Filtrer par véhicule",
                                    options=['Tous'] + list(VEHICLES.keys()),
                                    format_func=lambda x: 'Tous les véhicules' if x == 'Tous' else VEHICLES[x]['name'])
    
    with col2:
        filter_type = st.selectbox("Filtrer par type",
                                 options=['Tous', 'professional', 'private'],
                                 format_func=lambda x: {'Tous': 'Tous les types', 
                                                       'professional': 'Professionnel', 
                                                       'private': 'Privé'}[x])
    
    with col3:
        filter_driver = st.text_input("Rechercher par utilisateur")
    
    # Application des filtres
    filtered_trips = st.session_state.trips.copy()
    
    if filter_vehicle != 'Tous':
        filtered_trips = [trip for trip in filtered_trips if trip['vehicle'] == filter_vehicle]
    
    if filter_type != 'Tous':
        filtered_trips = [trip for trip in filtered_trips if trip['trip_type'] == filter_type]
    
    if filter_driver:
        filtered_trips = [trip for trip in filtered_trips if filter_driver.lower() in trip['driver_name'].lower()]
    
            # Affichage des résultats
    if filtered_trips:
        # Trier par date de départ (plus récent en premier)
        filtered_trips.sort(key=lambda x: x['departure_date'], reverse=True)
        
        # Préparer les données pour l'affichage
        display_data = []
        for trip in filtered_trips:
            try:
                departure_str = trip['departure_date'].strftime('%d/%m/%Y %H:%M') if isinstance(trip['departure_date'], datetime) else str(trip['departure_date'])
                return_str = trip['return_date'].strftime('%d/%m/%Y %H:%M') if isinstance(trip['return_date'], datetime) else str(trip['return_date'])
            except:
                departure_str = str(trip['departure_date'])
                return_str = str(trip['return_date'])
                
            display_data.append({
                'Date': departure_str,
                'Véhicule': f"{trip['vehicle_name']}\n{trip['vehicle_plate']}",
                'Utilisateur': trip['driver_name'],
                'Matricule': trip['driver_registration'],
                'Type': 'Prof.' if trip['trip_type'] == 'professional' else 'Privé',
                'Objet': trip['trip_purpose'],
                'Distance (km)': f"{trip['distance_traveled']:,}",
                'Péage': f"{trip['toll_amount']:,} F CFA" if trip['used_toll'] else 'Non',
                'Retour': return_str,
                'ID': trip['id']
            })
        
        df = pd.DataFrame(display_data)
        
        # Affichage du tableau
        st.dataframe(
            df.drop('ID', axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        # Sélection d'un déplacement pour modification/suppression
        st.subheader("Actions sur les déplacements")
        
        # Sélection par ID
        if filtered_trips:
            trip_options = []
            for trip in filtered_trips:
                try:
                    date_str = trip['departure_date'].strftime('%d/%m/%Y') if isinstance(trip['departure_date'], datetime) else str(trip['departure_date'])
                except:
                    date_str = str(trip['departure_date'])
                trip_options.append((str(trip['id']), f"ID {trip['id']} - {trip['driver_name']} - {date_str}"))
            
            selected_option = st.selectbox(
                "Choisir un déplacement à modifier/supprimer:",
                options=trip_options,
                format_func=lambda x: x[1] if x else "",
                index=None,
                placeholder="Sélectionner un déplacement..."
            )
            
            if selected_option:
                selected_trip_id = int(selected_option[0])
                
                col_action1, col_action2 = st.columns(2)
                
                with col_action1:
                    if st.button("✏️ Modifier le déplacement", type="secondary"):
                        st.session_state.editing_trip_id = selected_trip_id
                        st.session_state.show_edit_form = True
                
                with col_action2:
                    if st.button("🗑️ Supprimer le déplacement", type="secondary"):
                        st.session_state.deleting_trip_id = selected_trip_id
                        st.session_state.show_delete_confirm = True
    else:
        st.warning("Aucun déplacement ne correspond aux filtres sélectionnés.")
    
    # Modal de modification
    if st.session_state.get('show_edit_form', False):
        edit_trip_modal()
    
    # Modal de suppression
    if st.session_state.get('show_delete_confirm', False):
        delete_trip_modal()

# Modal de modification d'un déplacement
def edit_trip_modal():
    if 'editing_trip_id' not in st.session_state:
        return
        
    st.subheader("Modifier le déplacement")
    
    trip_id = st.session_state.editing_trip_id
    trip = next((t for t in st.session_state.trips if t['id'] == trip_id), None)
    
    if not trip:
        st.error("Déplacement non trouvé.")
        return
    
    with st.form("edit_trip_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vehicle = st.selectbox("Véhicule *", 
                                 options=['ford', 'renault'],
                                 index=['ford', 'renault'].index(trip['vehicle']),
                                 format_func=lambda x: VEHICLES[x]['name'])
            
            driver_name = st.text_input("Prénom et Nom de l'utilisateur *", value=trip['driver_name'])
            
            departure_edit_col1, departure_edit_time_col1 = st.columns(2)
            with departure_edit_col1:
                departure_date_part = st.date_input("Date de sortie *", value=trip['departure_date'].date(), key="edit_dep_date")
            with departure_edit_time_col1:
                departure_time_part = st.time_input("Heure de sortie *", value=trip['departure_date'].time(), key="edit_dep_time")
            departure_date = datetime.combine(departure_date_part, departure_time_part)
        
        with col2:
            driver_registration = st.text_input("Matricule de l'utilisateur *", value=trip['driver_registration'])
            
            trip_type = st.selectbox("Type de sortie *",
                                   options=['professional', 'private'],
                                   index=['professional', 'private'].index(trip['trip_type']),
                                   format_func=lambda x: {'professional': 'Professionnelle', 'private': 'Privée'}[x])
            
            return_edit_col1, return_edit_time_col1 = st.columns(2)
            with return_edit_col1:
                return_date_part = st.date_input("Date de retour *", value=trip['return_date'].date(), key="edit_ret_date")
            with return_edit_time_col1:
                return_time_part = st.time_input("Heure de retour *", value=trip['return_date'].time(), key="edit_ret_time")
            return_date = datetime.combine(return_date_part, return_time_part)
        
        with col3:
            initial_km = st.number_input("Kilométrage initial *", min_value=0, step=1, value=trip['initial_km'], key="edit_initial_km")
            
            final_km = st.number_input("Kilométrage final *", min_value=0, step=1, value=trip['final_km'], key="edit_final_km")
            
            # Calcul automatique de la distance avec mise à jour en temps réel
            if initial_km and final_km and final_km >= initial_km:
                distance_traveled = final_km - initial_km
                st.success(f"✅ Kilomètres parcourus : **{distance_traveled:,} km**")
            elif initial_km and final_km and final_km < initial_km:
                st.error("❌ Le kilométrage final ne peut pas être inférieur au kilométrage initial")
                distance_traveled = 0
            else:
                st.info("ℹ️ Kilomètres parcourus : En attente des valeurs...")
                distance_traveled = 0
        
        trip_purpose = st.text_input("Objet du déplacement *", value=trip['trip_purpose'])
        itinerary = st.text_area("Itinéraire", value=trip.get('itinerary', ''))
        
        # Gestion du péage
        used_toll = st.checkbox("Passage par le péage", value=trip['used_toll'])
        toll_amount = trip['toll_amount']
        toll_direction = trip['toll_direction']
        
        if used_toll:
            col_toll1, col_toll2 = st.columns(2)
            with col_toll1:
                toll_amount = st.number_input("Montant payé au péage (F CFA)", min_value=0, step=100, value=toll_amount)
            with col_toll2:
                toll_direction = st.selectbox("Direction",
                                            options=['aller', 'retour', 'aller-retour'],
                                            index=['aller', 'retour', 'aller-retour'].index(toll_direction),
                                            format_func=lambda x: {'aller': 'Aller seulement', 
                                                                  'retour': 'Retour seulement', 
                                                                  'aller-retour': 'Aller-Retour'}[x])
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.form_submit_button("Annuler", use_container_width=True):
                st.session_state.show_edit_form = False
                st.rerun()
        
        with col_btn2:
            if st.form_submit_button("Sauvegarder", type="primary", use_container_width=True):
                # Validation
                if not all([vehicle, driver_name, driver_registration, trip_type, trip_purpose]):
                    st.error("Veuillez remplir tous les champs obligatoires (*)")
                    return
                
                if return_date < departure_date:
                    st.error("La date de retour ne peut pas être antérieure à la date de sortie.")
                    return
                
                if final_km < initial_km:
                    st.error("Le kilométrage final ne peut pas être inférieur au kilométrage initial.")
                    return
                
                # Ajuster l'usage du péage
                # Rembourser l'ancien montant
                if trip['used_toll'] and trip['toll_amount'] > 0:
                    st.session_state.toll_usage[trip['vehicle']] -= trip['toll_amount']
                
                # Vérifier le nouveau montant
                if used_toll and toll_amount > 0:
                    current_toll_usage = st.session_state.toll_usage[vehicle]
                    remaining_balance = 30000 - current_toll_usage
                    
                    if toll_amount > remaining_balance:
                        st.error(f"Solde insuffisant sur la carte de péage ! Solde restant : {remaining_balance:,} F CFA")
                        # Remettre l'ancien montant
                        if trip['used_toll'] and trip['toll_amount'] > 0:
                            st.session_state.toll_usage[trip['vehicle']] += trip['toll_amount']
                        return
                    
                    st.session_state.toll_usage[vehicle] += toll_amount
                
                # Mettre à jour le déplacement
                trip_index = next(i for i, t in enumerate(st.session_state.trips) if t['id'] == trip_id)
                st.session_state.trips[trip_index].update({
                    'vehicle': vehicle,
                    'vehicle_name': VEHICLES[vehicle]['name'],
                    'vehicle_plate': VEHICLES[vehicle]['plate'],
                    'driver_name': driver_name,
                    'driver_registration': driver_registration,
                    'departure_date': departure_date,
                    'return_date': return_date,
                    'initial_km': initial_km,
                    'final_km': final_km,
                    'distance_traveled': distance_traveled,
                    'trip_type': trip_type,
                    'trip_purpose': trip_purpose,
                    'itinerary': itinerary,
                    'used_toll': used_toll,
                    'toll_amount': toll_amount,
                    'toll_direction': toll_direction
                })
                
                st.session_state.show_edit_form = False
                st.success("Déplacement modifié avec succès !")
                st.rerun()

# Modal de confirmation de suppression
def delete_trip_modal():
    if 'deleting_trip_id' not in st.session_state:
        return
        
    st.subheader("⚠️ Confirmer la suppression")
    st.warning("Êtes-vous sûr de vouloir supprimer ce déplacement ? Cette action est irréversible.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Annuler", use_container_width=True):
            st.session_state.show_delete_confirm = False
            st.rerun()
    
    with col2:
        if st.button("Supprimer", type="primary", use_container_width=True):
            trip_id = st.session_state.deleting_trip_id
            trip_index = next((i for i, t in enumerate(st.session_state.trips) if t['id'] == trip_id), None)
            
            if trip_index is not None:
                trip = st.session_state.trips[trip_index]
                
                # Rembourser le montant du péage si applicable
                if trip['used_toll'] and trip['toll_amount'] > 0:
                    st.session_state.toll_usage[trip['vehicle']] -= trip['toll_amount']
                    if st.session_state.toll_usage[trip['vehicle']] < 0:
                        st.session_state.toll_usage[trip['vehicle']] = 0
                
                # Supprimer le déplacement
                del st.session_state.trips[trip_index]
                
                st.session_state.show_delete_confirm = False
                st.success("Déplacement supprimé avec succès !")
                st.rerun()

# Application principale
def main():
    init_session_state()
    
    # Vérification de l'authentification
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Interface principale
    show_header()
    
    # Navigation par onglets
    tab1, tab2, tab3 = st.tabs(["➕ Nouveau Déplacement", "📊 Tableau de Bord", "📋 Historique"])
    
    with tab1:
        add_trip_page()
    
    with tab2:
        dashboard_page()
    
    with tab3:
        history_page()

if __name__ == "__main__":
    main()
