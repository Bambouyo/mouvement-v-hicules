"""
╔══════════════════════════════════════════════════════════════════════╗
║         SALAM FLEET MANAGER — Gestion Parc Automobile               ║
║         Maintenance · Rotations · Alertes · Rapports                ║
╚══════════════════════════════════════════════════════════════════════╝
Dépendances : streamlit, pandas, plotly, pillow
Installation : pip install streamlit pandas plotly pillow
Lancement    : streamlit run parc_automobile.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Fleet Manager",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS CUSTOM — thème professionnel sombre-acier
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

:root {
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --accent: #f78166;
    --accent2: #3fb950;
    --accent3: #d29922;
    --accent4: #58a6ff;
    --text: #e6edf3;
    --muted: #8b949e;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

h1, h2, h3, h4 {
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.04em;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    transition: border-color .2s;
}
[data-testid="metric-container"]:hover { border-color: var(--accent4); }
[data-testid="stMetricLabel"]  { color: var(--muted) !important; font-size:.75rem; text-transform:uppercase; letter-spacing:.08em; }
[data-testid="stMetricValue"]  { color: var(--text) !important; font-family:'Rajdhani',sans-serif; font-size:2rem; }

/* Dataframes */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
.stDataFrame thead { background: var(--surface) !important; }

/* Buttons */
.stButton > button {
    background: var(--accent4) !important;
    color: #0d1117 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: .05em !important;
    transition: opacity .2s !important;
}
.stButton > button:hover { opacity: .85 !important; }

/* Expander */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
}

/* Tabs */
[data-baseweb="tab-list"] { background: var(--surface) !important; border-radius: 8px; }
[data-baseweb="tab"] { color: var(--muted) !important; }
[aria-selected="true"] { color: var(--accent4) !important; border-bottom: 2px solid var(--accent4) !important; }

/* Inputs */
input, textarea, select, [data-baseweb="select"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}

/* Alert badges */
.badge-danger  { background:#f78166;color:#0d1117;padding:2px 8px;border-radius:20px;font-size:.75rem;font-weight:700; }
.badge-warning { background:#d29922;color:#0d1117;padding:2px 8px;border-radius:20px;font-size:.75rem;font-weight:700; }
.badge-ok      { background:#3fb950;color:#0d1117;padding:2px 8px;border-radius:20px;font-size:.75rem;font-weight:700; }

/* Section titles */
.section-title {
    font-family:'Rajdhani',sans-serif;
    font-size:1.4rem;font-weight:700;
    color:var(--accent4);
    border-left:4px solid var(--accent4);
    padding-left:.7rem;
    margin-bottom:1rem;
}

/* Scrollbar */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# BASE DE DONNÉES SQLITE
# ─────────────────────────────────────────────
DB_PATH = "fleet_manager.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS vehicules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        immatriculation TEXT UNIQUE NOT NULL,
        marque TEXT,
        modele TEXT,
        type_vehicule TEXT,
        annee INTEGER,
        carburant TEXT,
        kilometrage INTEGER DEFAULT 0,
        statut TEXT DEFAULT 'Disponible',
        date_acquisition TEXT,
        prochain_ct TEXT,
        prochain_vidange INTEGER,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS conducteurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT,
        service TEXT,
        telephone TEXT,
        permis TEXT,
        permis_expiration TEXT,
        actif INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS rotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicule_id INTEGER,
        conducteur_id INTEGER,
        destination TEXT,
        motif TEXT,
        km_depart INTEGER,
        km_retour INTEGER,
        date_depart TEXT,
        heure_depart TEXT,
        date_retour TEXT,
        heure_retour TEXT,
        statut TEXT DEFAULT 'En cours',
        observations TEXT,
        FOREIGN KEY(vehicule_id) REFERENCES vehicules(id),
        FOREIGN KEY(conducteur_id) REFERENCES conducteurs(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS maintenances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicule_id INTEGER,
        type_maintenance TEXT,
        description TEXT,
        date_intervention TEXT,
        km_intervention INTEGER,
        prestataire TEXT,
        cout REAL DEFAULT 0,
        statut TEXT DEFAULT 'Planifiée',
        date_prochaine TEXT,
        km_prochain INTEGER,
        pieces_changees TEXT,
        facture_ref TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(vehicule_id) REFERENCES vehicules(id)
    )""")

    # Données de démonstration
    c.execute("SELECT COUNT(*) FROM vehicules")
    if c.fetchone()[0] == 0:
        vehicules_demo = [
            ("DK-1234-AB","Toyota","Hilux","Pick-up",2021,"Diesel",45200,"Disponible","2021-03-10","2024-09-01",50000),
            ("DK-5678-CD","Hyundai","Tucson","SUV",2022,"Essence",28500,"Disponible","2022-01-15","2025-01-20",35000),
            ("DK-9012-EF","Mercedes","Sprinter","Minibus",2020,"Diesel",87300,"En mission","2020-06-01","2023-12-10",90000),
            ("DK-3456-GH","Renault","Duster","SUV",2023,"Diesel",12800,"Disponible","2023-05-20","2026-05-20",20000),
            ("DK-7890-IJ","Toyota","Land Cruiser","4x4",2019,"Diesel",112500,"Maintenance","2019-09-14","2023-09-01",115000),
            ("DK-2345-KL","Ford","Transit","Fourgon",2021,"Diesel",67400,"Disponible","2021-11-08","2024-11-08",70000),
        ]
        for v in vehicules_demo:
            c.execute("""INSERT INTO vehicules
                (immatriculation,marque,modele,type_vehicule,annee,carburant,kilometrage,statut,date_acquisition,prochain_ct,prochain_vidange)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", v)

        conducteurs_demo = [
            ("DIALLO","Amadou","Direction Générale","77 123 45 67","B","2026-08-15"),
            ("FALL","Fatou","Administration","78 234 56 78","B","2025-11-30"),
            ("NDIAYE","Ibrahima","Logistique","76 345 67 89","B,C","2027-02-20"),
            ("SOW","Moussa","Technique","77 456 78 90","B","2025-06-10"),
            ("CISSÉ","Mariama","Communication","78 567 89 01","B","2026-04-05"),
        ]
        for cd in conducteurs_demo:
            c.execute("""INSERT INTO conducteurs (nom,prenom,service,telephone,permis,permis_expiration)
                VALUES (?,?,?,?,?,?)""", cd)

        maintenances_demo = [
            (1,"Vidange","Vidange + filtre huile","2024-06-10",45000,"Garage Auto Dakar",35000,"Effectuée","2024-12-01",50000,"Filtre huile, huile moteur 5W40","FAC-001"),
            (2,"Pneumatiques","Remplacement 4 pneus","2024-07-15",28000,"Michelin Center",180000,"Effectuée",None,60000,"4x Michelin Primacy","FAC-002"),
            (3,"Révision générale","Révision 90 000 km","2024-05-20",87000,"Garage Mercedes Dakar",450000,"Effectuée","2024-11-20",100000,"Courroie, bougies, filtres","FAC-003"),
            (5,"Freins","Remplacement plaquettes avant","2024-08-01",112000,"Garage Sénégal Auto",65000,"Effectuée",None,120000,"Plaquettes Brembo","FAC-004"),
            (1,"Vidange","Vidange préventive","2024-12-01",50000,"Garage Auto Dakar",35000,"Planifiée",None,55000,None,None),
            (5,"Révision","Révision urgente — perte puissance","2024-09-10",112500,"Garage Mercedes Dakar",280000,"En cours",None,None,None,None),
        ]
        for m in maintenances_demo:
            c.execute("""INSERT INTO maintenances
                (vehicule_id,type_maintenance,description,date_intervention,km_intervention,
                 prestataire,cout,statut,date_prochaine,km_prochain,pieces_changees,facture_ref)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", m)

        rotations_demo = [
            (3,3,"Thiès","Livraison matériel",87100,87300,"2024-09-10","08:00","2024-09-10","17:30","Terminée","RAS"),
            (1,1,"Ziguinchor","Mission terrain",44800,45200,"2024-09-05","06:00","2024-09-08","19:00","Terminée","Piste pluie"),
            (2,5,"Dakar Centre","Réunion DG",28400,28500,"2024-09-12","09:00","2024-09-12","13:00","Terminée",""),
            (4,2,"Saint-Louis","Séminaire",12600,12800,"2024-09-13","07:00","2024-09-14","20:00","Terminée",""),
            (3,4,"Rufisque","Transport équipe",87300,None,"2024-09-15","08:00",None,None,"En cours",""),
        ]
        for r in rotations_demo:
            c.execute("""INSERT INTO rotations
                (vehicule_id,conducteur_id,destination,motif,km_depart,km_retour,
                 date_depart,heure_depart,date_retour,heure_retour,statut,observations)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", r)

    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def query(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = get_conn()
    conn.execute(sql, params)
    conn.commit()
    conn.close()

def get_vehicules():
    return query("SELECT * FROM vehicules ORDER BY immatriculation")

def get_conducteurs():
    return query("SELECT * FROM conducteurs WHERE actif=1 ORDER BY nom")

def get_vehicule_label(df_v):
    return {row.id: f"{row.immatriculation} — {row.marque} {row.modele}" for row in df_v.itertuples()}

def get_conducteur_label(df_c):
    return {row.id: f"{row.nom} {row.prenom} ({row.service})" for row in df_c.itertuples()}

def statut_badge(statut):
    colors = {
        "Disponible": "#3fb950", "En mission": "#58a6ff",
        "Maintenance": "#f78166", "Hors service": "#8b949e",
        "En cours": "#58a6ff", "Terminée": "#3fb950",
        "Planifiée": "#d29922", "Effectuée": "#3fb950",
        "Annulée": "#8b949e",
    }
    c = colors.get(statut, "#8b949e")
    return f'<span style="background:{c};color:#0d1117;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:700;">{statut}</span>'

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 1.5rem">
        <div style="font-family:'Rajdhani',sans-serif;font-size:1.8rem;font-weight:700;color:#58a6ff;">🚗 FLEET</div>
        <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;color:#8b949e;letter-spacing:.15em;">MANAGER PRO</div>
        <hr style="border-color:#30363d;margin-top:.8rem">
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio("Navigation", [
        "🏠  Tableau de Bord",
        "🚘  Véhicules",
        "🔧  Maintenance",
        "🔄  Rotations",
        "👤  Conducteurs",
        "📊  Rapports",
        "⚠️  Alertes",
    ], label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:.8rem;background:#161b22;border:1px solid #30363d;border-radius:8px;font-size:.8rem;color:#8b949e;">
        <b style="color:#e6edf3;">Fleet Manager Pro</b><br>
        Base SQLite locale<br>
        <span style="color:#3fb950;">● Connecté</span>
    </div>
    """, unsafe_allow_html=True)

page = menu.split("  ")[1]

# ═══════════════════════════════════════════════════════
# PAGE 1 — TABLEAU DE BORD
# ═══════════════════════════════════════════════════════
if page == "Tableau de Bord":
    st.markdown('<div class="section-title">TABLEAU DE BORD</div>', unsafe_allow_html=True)

    df_v   = get_vehicules()
    df_r   = query("SELECT * FROM rotations")
    df_m   = query("SELECT * FROM maintenances")
    df_c   = get_conducteurs()

    total_v    = len(df_v)
    dispo      = len(df_v[df_v.statut == "Disponible"])
    en_mission = len(df_v[df_v.statut == "En mission"])
    en_maint   = len(df_v[df_v.statut == "Maintenance"])
    cout_total = df_m[df_m.statut == "Effectuée"]["cout"].sum() if "cout" in df_m.columns else 0
    rotations_mois = len(df_r[df_r.date_depart >= str(date.today() - timedelta(days=30))]) if len(df_r) else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🚗 Total Véhicules", total_v)
    c2.metric("✅ Disponibles", dispo, delta=f"{dispo}/{total_v}")
    c3.metric("🔄 En Mission", en_mission)
    c4.metric("🔧 Maintenance", en_maint)
    c5.metric("👤 Conducteurs", len(df_c))
    c6.metric("💰 Coûts Maint.", f"{int(cout_total):,} FCFA".replace(",", " "))

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown('<div class="section-title">Répartition des Statuts</div>', unsafe_allow_html=True)
        counts = df_v["statut"].value_counts().reset_index()
        counts.columns = ["Statut", "Nb"]
        fig_pie = px.pie(
            counts, values="Nb", names="Statut",
            color="Statut",
            color_discrete_map={"Disponible":"#3fb950","En mission":"#58a6ff","Maintenance":"#f78166","Hors service":"#8b949e"},
            hole=.45,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e6edf3", legend_font_color="#e6edf3",
            margin=dict(t=20,b=20,l=0,r=0), height=280,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Coûts Maintenance par Type</div>', unsafe_allow_html=True)
        if len(df_m) > 0:
            df_m_eff = df_m[df_m.statut == "Effectuée"]
            if len(df_m_eff) > 0:
                cost_type = df_m_eff.groupby("type_maintenance")["cout"].sum().reset_index()
                fig_bar = px.bar(
                    cost_type, x="type_maintenance", y="cout",
                    labels={"type_maintenance":"Type","cout":"Coût (FCFA)"},
                    color="cout", color_continuous_scale=["#161b22","#58a6ff"],
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e6edf3", height=280,
                    xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"),
                    coloraxis_showscale=False, margin=dict(t=20,b=20),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown('<div class="section-title">État du Parc</div>', unsafe_allow_html=True)
    df_display = df_v[["immatriculation","marque","modele","type_vehicule","kilometrage","statut","prochain_ct"]].copy()
    df_display.columns = ["Immat.","Marque","Modèle","Type","Km","Statut","Prochain CT"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Alertes rapides
    today = date.today()
    alertes = []
    for _, row in df_v.iterrows():
        if row.prochain_ct:
            try:
                ct_date = datetime.strptime(row.prochain_ct, "%Y-%m-%d").date()
                if ct_date <= today + timedelta(days=30):
                    alertes.append(f"⚠️ CT expiré/proche pour **{row.immatriculation}** ({row.prochain_ct})")
            except: pass
        if row.prochain_vidange and row.kilometrage >= row.prochain_vidange - 500:
            alertes.append(f"🔧 Vidange à faire pour **{row.immatriculation}** ({int(row.prochain_vidange):,} km)")

    if alertes:
        st.markdown('<div class="section-title">⚠️ Alertes Actives</div>', unsafe_allow_html=True)
        for a in alertes:
            st.warning(a)

# ═══════════════════════════════════════════════════════
# PAGE 2 — VÉHICULES
# ═══════════════════════════════════════════════════════
elif page == "Véhicules":
    st.markdown('<div class="section-title">GESTION DES VÉHICULES</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Ajouter", "✏️ Modifier / Supprimer"])

    with tab1:
        df_v = get_vehicules()
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            search = st.text_input("🔍 Rechercher (immatriculation, marque…)", "")
        with col_f2:
            filtre_statut = st.selectbox("Statut", ["Tous","Disponible","En mission","Maintenance","Hors service"])

        if search:
            mask = (
                df_v["immatriculation"].str.contains(search, case=False, na=False) |
                df_v["marque"].str.contains(search, case=False, na=False) |
                df_v["modele"].str.contains(search, case=False, na=False)
            )
            df_v = df_v[mask]
        if filtre_statut != "Tous":
            df_v = df_v[df_v.statut == filtre_statut]

        cols_show = ["immatriculation","marque","modele","type_vehicule","annee","carburant","kilometrage","statut","prochain_ct","prochain_vidange"]
        labels    = ["Immat.","Marque","Modèle","Type","Année","Carburant","Km","Statut","Prochain CT","Prochain Vidange (km)"]
        df_show = df_v[cols_show].copy()
        df_show.columns = labels
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("#### Nouveau Véhicule")
        c1, c2, c3 = st.columns(3)
        immat  = c1.text_input("Immatriculation *", placeholder="DK-XXXX-XX")
        marque = c2.text_input("Marque *")
        modele = c3.text_input("Modèle *")
        c4, c5, c6 = st.columns(3)
        type_v   = c4.selectbox("Type", ["Berline","SUV","Pick-up","4x4","Minibus","Fourgon","Camion","Moto"])
        annee    = c5.number_input("Année", 2000, date.today().year, date.today().year)
        carburant= c6.selectbox("Carburant", ["Diesel","Essence","Hybride","Électrique","GPL"])
        c7, c8, c9 = st.columns(3)
        km       = c7.number_input("Kilométrage actuel", 0, step=100)
        dt_acq   = c8.date_input("Date acquisition")
        statut_v = c9.selectbox("Statut initial", ["Disponible","Maintenance","Hors service"])
        c10, c11 = st.columns(2)
        prochain_ct      = c10.date_input("Prochain CT", value=date.today() + timedelta(days=365))
        prochain_vidange = c11.number_input("Prochain vidange (km)", 0, step=1000)
        notes = st.text_area("Notes / observations")

        if st.button("💾 Enregistrer le Véhicule"):
            if immat and marque and modele:
                try:
                    execute("""INSERT INTO vehicules
                        (immatriculation,marque,modele,type_vehicule,annee,carburant,kilometrage,
                         statut,date_acquisition,prochain_ct,prochain_vidange,notes)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (immat, marque, modele, type_v, annee, carburant, km,
                         statut_v, str(dt_acq), str(prochain_ct), int(prochain_vidange), notes))
                    st.success(f"✅ Véhicule **{immat}** ajouté avec succès !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
            else:
                st.warning("Renseignez au minimum l'immatriculation, la marque et le modèle.")

    with tab3:
        df_v = get_vehicules()
        labels_v = get_vehicule_label(df_v)
        v_sel = st.selectbox("Sélectionner un véhicule", list(labels_v.values()))
        v_id  = [k for k, val in labels_v.items() if val == v_sel]
        if v_id:
            v_id = v_id[0]
            row  = df_v[df_v.id == v_id].iloc[0]
            st.markdown("---")
            c1, c2 = st.columns(2)
            new_km     = c1.number_input("Kilométrage", value=int(row.kilometrage), step=100)
            new_statut = c2.selectbox("Statut", ["Disponible","En mission","Maintenance","Hors service"],
                                       index=["Disponible","En mission","Maintenance","Hors service"].index(row.statut) if row.statut in ["Disponible","En mission","Maintenance","Hors service"] else 0)
            c3, c4 = st.columns(2)
            prochain_ct_edit = c3.date_input("Prochain CT", value=datetime.strptime(row.prochain_ct, "%Y-%m-%d").date() if row.prochain_ct else date.today())
            prochain_vid_edit= c4.number_input("Prochain vidange (km)", value=int(row.prochain_vidange) if row.prochain_vidange else 0, step=1000)
            new_notes = st.text_area("Notes", value=row.notes if row.notes else "")

            col_upd, col_del = st.columns([3, 1])
            if col_upd.button("💾 Mettre à jour"):
                execute("""UPDATE vehicules SET kilometrage=?,statut=?,prochain_ct=?,prochain_vidange=?,notes=? WHERE id=?""",
                        (new_km, new_statut, str(prochain_ct_edit), prochain_vid_edit, new_notes, v_id))
                st.success("✅ Véhicule mis à jour !")
                st.rerun()
            if col_del.button("🗑️ Supprimer", type="secondary"):
                execute("DELETE FROM vehicules WHERE id=?", (v_id,))
                st.warning("Véhicule supprimé.")
                st.rerun()

# ═══════════════════════════════════════════════════════
# PAGE 3 — MAINTENANCE
# ═══════════════════════════════════════════════════════
elif page == "Maintenance":
    st.markdown('<div class="section-title">GESTION DE LA MAINTENANCE</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Historique", "➕ Planifier / Enregistrer", "📈 Coûts"])

    with tab1:
        df_m = query("""
            SELECT m.id, v.immatriculation, v.marque||' '||v.modele AS vehicule,
                   m.type_maintenance, m.description, m.date_intervention,
                   m.km_intervention, m.prestataire, m.cout, m.statut,
                   m.date_prochaine, m.km_prochain, m.pieces_changees, m.facture_ref
            FROM maintenances m JOIN vehicules v ON m.vehicule_id=v.id
            ORDER BY m.date_intervention DESC
        """)
        f1, f2 = st.columns([2, 1])
        search_m = f1.text_input("🔍 Rechercher")
        filtre_s = f2.selectbox("Statut", ["Tous","Planifiée","En cours","Effectuée","Annulée"])

        if search_m:
            mask = (df_m["immatriculation"].str.contains(search_m, case=False, na=False) |
                    df_m["type_maintenance"].str.contains(search_m, case=False, na=False) |
                    df_m["vehicule"].str.contains(search_m, case=False, na=False))
            df_m = df_m[mask]
        if filtre_s != "Tous":
            df_m = df_m[df_m.statut == filtre_s]

        st.dataframe(df_m, use_container_width=True, hide_index=True)
        total_cout = df_m[df_m.statut == "Effectuée"]["cout"].sum()
        st.info(f"💰 Coût total des interventions effectuées (filtre actif) : **{int(total_cout):,} FCFA**".replace(",", " "))

    with tab2:
        st.markdown("#### Nouvelle Intervention")
        df_v = get_vehicules()
        labels_v = get_vehicule_label(df_v)
        v_sel = st.selectbox("Véhicule *", list(labels_v.values()), key="maint_v")
        v_id  = [k for k, val in labels_v.items() if val == v_sel][0]

        c1, c2 = st.columns(2)
        type_m = c1.selectbox("Type d'intervention *", [
            "Vidange","Révision générale","Pneumatiques","Freins","Batterie",
            "Climatisation","Carrosserie","Électricité","Contrôle technique","Autre"
        ])
        statut_m = c2.selectbox("Statut", ["Planifiée","En cours","Effectuée","Annulée"])

        desc_m = st.text_input("Description")
        c3, c4, c5 = st.columns(3)
        date_m     = c3.date_input("Date intervention")
        km_m       = c4.number_input("Km au moment de l'intervention", 0, step=100)
        prestataire= c5.text_input("Prestataire / Garage")
        c6, c7 = st.columns(2)
        cout_m     = c6.number_input("Coût (FCFA)", 0, step=1000)
        facture    = c7.text_input("Réf. Facture")
        pieces     = st.text_input("Pièces changées")
        c8, c9 = st.columns(2)
        date_proch = c8.date_input("Prochaine intervention (date)", value=date.today() + timedelta(days=180))
        km_proch   = c9.number_input("Prochaine intervention (km)", 0, step=1000)

        if st.button("💾 Enregistrer l'Intervention"):
            execute("""INSERT INTO maintenances
                (vehicule_id,type_maintenance,description,date_intervention,km_intervention,
                 prestataire,cout,statut,date_prochaine,km_prochain,pieces_changees,facture_ref)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (v_id, type_m, desc_m, str(date_m), km_m, prestataire, cout_m,
                 statut_m, str(date_proch), km_proch, pieces, facture))
            if statut_m in ["En cours","Planifiée"]:
                execute("UPDATE vehicules SET statut='Maintenance' WHERE id=?", (v_id,))
            elif statut_m == "Effectuée":
                execute("UPDATE vehicules SET kilometrage=MAX(kilometrage,?),prochain_vidange=? WHERE id=?",
                        (km_m, km_proch if km_proch > 0 else None, v_id))
            st.success("✅ Intervention enregistrée !")
            st.rerun()

    with tab3:
        df_m_all = query("""
            SELECT m.*, v.immatriculation, v.marque||' '||v.modele AS vehicule
            FROM maintenances m JOIN vehicules v ON m.vehicule_id=v.id
            WHERE m.statut='Effectuée'
        """)
        if len(df_m_all) > 0:
            col_a, col_b = st.columns(2)
            with col_a:
                cost_by_v = df_m_all.groupby("vehicule")["cout"].sum().reset_index()
                fig1 = px.bar(cost_by_v, x="vehicule", y="cout",
                              title="Coût par Véhicule",
                              labels={"vehicule":"Véhicule","cout":"Coût (FCFA)"},
                              color="cout", color_continuous_scale=["#161b22","#f78166"])
                fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="#e6edf3", height=300,
                                   xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"),
                                   coloraxis_showscale=False)
                st.plotly_chart(fig1, use_container_width=True)
            with col_b:
                cost_by_t = df_m_all.groupby("type_maintenance")["cout"].sum().reset_index()
                fig2 = px.pie(cost_by_t, values="cout", names="type_maintenance",
                              title="Répartition par Type",
                              color_discrete_sequence=px.colors.qualitative.Set3)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                   font_color="#e6edf3", height=300)
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucune intervention effectuée enregistrée.")

# ═══════════════════════════════════════════════════════
# PAGE 4 — ROTATIONS
# ═══════════════════════════════════════════════════════
elif page == "Rotations":
    st.markdown('<div class="section-title">GESTION DES ROTATIONS</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Journal", "➕ Nouvelle Rotation", "✅ Clôturer"])

    with tab1:
        df_rot = query("""
            SELECT r.id, v.immatriculation, v.marque||' '||v.modele AS vehicule,
                   c.nom||' '||c.prenom AS conducteur, c.service,
                   r.destination, r.motif, r.km_depart, r.km_retour,
                   r.date_depart, r.heure_depart, r.date_retour, r.heure_retour,
                   r.statut, r.observations
            FROM rotations r
            JOIN vehicules v ON r.vehicule_id=v.id
            JOIN conducteurs c ON r.conducteur_id=c.id
            ORDER BY r.date_depart DESC
        """)
        col_f1, col_f2 = st.columns([3, 1])
        search_r = col_f1.text_input("🔍 Rechercher (destination, conducteur…)")
        filtre_r = col_f2.selectbox("Statut", ["Tous","En cours","Terminée","Annulée"])

        if search_r:
            mask = (df_rot["destination"].str.contains(search_r, case=False, na=False) |
                    df_rot["conducteur"].str.contains(search_r, case=False, na=False) |
                    df_rot["vehicule"].str.contains(search_r, case=False, na=False))
            df_rot = df_rot[mask]
        if filtre_r != "Tous":
            df_rot = df_rot[df_rot.statut == filtre_r]

        km_parcourus = 0
        for _, row in df_rot.iterrows():
            if row.km_retour and row.km_depart:
                km_parcourus += int(row.km_retour) - int(row.km_depart)

        st.dataframe(df_rot, use_container_width=True, hide_index=True)
        st.info(f"🛣️ Km parcourus (filtre actif) : **{km_parcourus:,} km**".replace(",", " "))

    with tab2:
        df_v = get_vehicules()
        df_c = get_conducteurs()
        labels_v = get_vehicule_label(df_v[df_v.statut == "Disponible"])
        labels_c = get_conducteur_label(df_c)

        if not labels_v:
            st.warning("⚠️ Aucun véhicule disponible en ce moment.")
        else:
            c1, c2 = st.columns(2)
            v_sel = c1.selectbox("Véhicule disponible *", list(labels_v.values()))
            c_sel = c2.selectbox("Conducteur *", list(labels_c.values()))
            v_id  = [k for k, val in labels_v.items() if val == v_sel][0]
            c_id  = [k for k, val in labels_c.items() if val == c_sel][0]

            dest    = st.text_input("Destination *")
            motif   = st.text_input("Motif de la mission")
            c3, c4, c5, c6 = st.columns(4)
            dt_dep  = c3.date_input("Date départ")
            hr_dep  = c4.time_input("Heure départ")
            km_dep  = c5.number_input("Km départ", 0, step=10)
            obs     = c6.text_input("Observations")

            km_v = int(df_v[df_v.id == v_id].iloc[0].kilometrage)
            st.caption(f"ℹ️ Kilométrage actuel du véhicule : **{km_v:,} km**".replace(",", " "))

            if st.button("🚀 Lancer la Rotation"):
                if dest:
                    execute("""INSERT INTO rotations
                        (vehicule_id,conducteur_id,destination,motif,km_depart,
                         date_depart,heure_depart,statut,observations)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                        (v_id, c_id, dest, motif, km_dep if km_dep > 0 else km_v,
                         str(dt_dep), str(hr_dep), "En cours", obs))
                    execute("UPDATE vehicules SET statut='En mission' WHERE id=?", (v_id,))
                    st.success(f"✅ Rotation lancée vers **{dest}** !")
                    st.rerun()
                else:
                    st.warning("Renseignez la destination.")

    with tab3:
        df_en_cours = query("""
            SELECT r.id, v.immatriculation, v.marque||' '||v.modele AS vehicule,
                   c.nom||' '||c.prenom AS conducteur,
                   r.destination, r.km_depart, r.date_depart,
                   r.vehicule_id
            FROM rotations r
            JOIN vehicules v ON r.vehicule_id=v.id
            JOIN conducteurs c ON r.conducteur_id=c.id
            WHERE r.statut='En cours'
        """)
        if len(df_en_cours) == 0:
            st.info("Aucune rotation en cours.")
        else:
            rot_sel = st.selectbox("Rotation à clôturer",
                [f"#{row.id} — {row.vehicule} vers {row.destination} (départ {row.date_depart})"
                 for row in df_en_cours.itertuples()])
            rot_id = int(rot_sel.split("#")[1].split(" ")[0])
            rot_row = df_en_cours[df_en_cours.id == rot_id].iloc[0]

            c1, c2, c3 = st.columns(3)
            dt_ret   = c1.date_input("Date retour", value=date.today())
            hr_ret   = c2.time_input("Heure retour")
            km_ret   = c3.number_input("Km retour", int(rot_row.km_depart), step=10)
            obs_ret  = st.text_input("Observations retour")
            statut_r = st.selectbox("Statut final", ["Terminée","Annulée"])

            km_parcourus = km_ret - int(rot_row.km_depart) if km_ret > 0 else 0
            st.caption(f"🛣️ Distance parcourue : **{km_parcourus:,} km**".replace(",", " "))

            if st.button("✅ Clôturer la Rotation"):
                execute("""UPDATE rotations SET
                    km_retour=?,date_retour=?,heure_retour=?,statut=?,observations=?
                    WHERE id=?""",
                    (km_ret, str(dt_ret), str(hr_ret), statut_r, obs_ret, rot_id))
                execute("""UPDATE vehicules SET statut='Disponible', kilometrage=MAX(kilometrage,?)
                    WHERE id=?""", (km_ret, int(rot_row.vehicule_id)))
                st.success("✅ Rotation clôturée, véhicule remis disponible !")
                st.rerun()

# ═══════════════════════════════════════════════════════
# PAGE 5 — CONDUCTEURS
# ═══════════════════════════════════════════════════════
elif page == "Conducteurs":
    st.markdown('<div class="section-title">GESTION DES CONDUCTEURS</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter / Modifier"])

    with tab1:
        df_c = query("""
            SELECT c.id, c.nom, c.prenom, c.service, c.telephone, c.permis,
                   c.permis_expiration, c.actif,
                   COUNT(r.id) AS nb_missions,
                   COALESCE(SUM(r.km_retour - r.km_depart),0) AS km_total
            FROM conducteurs c
            LEFT JOIN rotations r ON r.conducteur_id=c.id AND r.statut='Terminée'
            GROUP BY c.id
            ORDER BY c.nom
        """)
        today = date.today()
        df_c["Permis OK"] = df_c["permis_expiration"].apply(
            lambda x: "✅" if x and datetime.strptime(x, "%Y-%m-%d").date() > today else "⚠️ Expiré"
        )
        st.dataframe(df_c[["nom","prenom","service","telephone","permis","permis_expiration","Permis OK","nb_missions","km_total"]],
                     use_container_width=True, hide_index=True)

    with tab2:
        col_new, col_edit = st.columns(2)

        with col_new:
            st.markdown("##### Nouveau Conducteur")
            nom  = st.text_input("Nom *")
            pren = st.text_input("Prénom")
            serv = st.text_input("Service / Direction")
            tel  = st.text_input("Téléphone")
            perm = st.text_input("Catégorie(s) permis")
            perm_exp = st.date_input("Expiration permis", value=date.today() + timedelta(days=365))
            if st.button("💾 Ajouter Conducteur"):
                if nom:
                    execute("""INSERT INTO conducteurs (nom,prenom,service,telephone,permis,permis_expiration)
                        VALUES (?,?,?,?,?,?)""",
                        (nom.upper(), pren, serv, tel, perm, str(perm_exp)))
                    st.success(f"✅ {nom.upper()} ajouté !")
                    st.rerun()

        with col_edit:
            st.markdown("##### Modifier / Désactiver")
            df_cc = get_conducteurs()
            labels_c = {row.id: f"{row.nom} {row.prenom}" for row in df_cc.itertuples()}
            if labels_c:
                c_sel = st.selectbox("Conducteur", list(labels_c.values()), key="c_edit")
                c_id  = [k for k, v in labels_c.items() if v == c_sel][0]
                c_row = df_cc[df_cc.id == c_id].iloc[0]
                new_serv    = st.text_input("Service", value=c_row.service or "")
                new_tel     = st.text_input("Téléphone", value=c_row.telephone or "")
                new_perm_exp= st.date_input("Expiration permis",
                    value=datetime.strptime(c_row.permis_expiration, "%Y-%m-%d").date() if c_row.permis_expiration else date.today())
                col_u, col_d = st.columns(2)
                if col_u.button("💾 Mettre à jour", key="c_upd"):
                    execute("UPDATE conducteurs SET service=?,telephone=?,permis_expiration=? WHERE id=?",
                            (new_serv, new_tel, str(new_perm_exp), c_id))
                    st.success("✅ Mis à jour !")
                    st.rerun()
                if col_d.button("🚫 Désactiver", key="c_deact"):
                    execute("UPDATE conducteurs SET actif=0 WHERE id=?", (c_id,))
                    st.warning("Conducteur désactivé.")
                    st.rerun()

# ═══════════════════════════════════════════════════════
# PAGE 6 — RAPPORTS
# ═══════════════════════════════════════════════════════
elif page == "Rapports":
    st.markdown('<div class="section-title">RAPPORTS & STATISTIQUES</div>', unsafe_allow_html=True)

    df_v = get_vehicules()
    df_rot_all = query("""
        SELECT r.*, v.immatriculation, v.marque||' '||v.modele AS vehicule,
               c.nom||' '||c.prenom AS conducteur
        FROM rotations r
        JOIN vehicules v ON r.vehicule_id=v.id
        JOIN conducteurs c ON r.conducteur_id=c.id
    """)
    df_m_all = query("""
        SELECT m.*, v.immatriculation, v.marque||' '||v.modele AS vehicule
        FROM maintenances m JOIN vehicules v ON m.vehicule_id=v.id
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🚗 Utilisation par Véhicule")
        usage = df_rot_all[df_rot_all.statut == "Terminée"].groupby("vehicule").agg(
            missions=("id","count"),
        ).reset_index()
        if len(usage) > 0:
            fig = px.bar(usage, x="vehicule", y="missions",
                         color="missions", color_continuous_scale=["#161b22","#58a6ff"],
                         labels={"vehicule":"Véhicule","missions":"Nb missions"})
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#e6edf3", height=300, coloraxis_showscale=False,
                              xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 👤 Missions par Conducteur")
        by_cond = df_rot_all[df_rot_all.statut == "Terminée"].groupby("conducteur").size().reset_index(name="missions")
        if len(by_cond) > 0:
            fig2 = px.bar(by_cond, x="conducteur", y="missions",
                          color="missions", color_continuous_scale=["#161b22","#3fb950"])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#e6edf3", height=300, coloraxis_showscale=False,
                               xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"))
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 💰 Évolution des Coûts de Maintenance")
    df_m_eff = df_m_all[df_m_all.statut == "Effectuée"].copy()
    if len(df_m_eff) > 0:
        df_m_eff["date_intervention"] = pd.to_datetime(df_m_eff["date_intervention"])
        df_m_eff["mois"] = df_m_eff["date_intervention"].dt.to_period("M").astype(str)
        cost_mois = df_m_eff.groupby("mois")["cout"].sum().reset_index()
        fig3 = px.line(cost_mois, x="mois", y="cout",
                       markers=True,
                       labels={"mois":"Mois","cout":"Coût (FCFA)"},
                       color_discrete_sequence=["#f78166"])
        fig3.update_traces(line=dict(width=2.5), marker=dict(size=8))
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#e6edf3", height=280,
                           xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"))
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### 📋 Résumé Global")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total véhicules", len(df_v))
    c2.metric("Total rotations", len(df_rot_all))
    c3.metric("Total maintenances", len(df_m_all))
    total_cost = df_m_eff["cout"].sum() if len(df_m_eff) > 0 else 0
    c4.metric("Coût total maintenance", f"{int(total_cost):,} FCFA".replace(",", " "))

# ═══════════════════════════════════════════════════════
# PAGE 7 — ALERTES
# ═══════════════════════════════════════════════════════
elif page == "Alertes":
    st.markdown('<div class="section-title">CENTRE D\'ALERTES</div>', unsafe_allow_html=True)

    today = date.today()
    df_v  = get_vehicules()
    df_c  = get_conducteurs()

    alertes_ct, alertes_vid, alertes_perm, alertes_maint = [], [], [], []

    # Contrôles techniques
    for _, v in df_v.iterrows():
        if v.prochain_ct:
            try:
                ct = datetime.strptime(v.prochain_ct, "%Y-%m-%d").date()
                delta = (ct - today).days
                if delta < 0:
                    alertes_ct.append(("🔴 EXPIRÉ", v.immatriculation, v.marque+" "+v.modele, v.prochain_ct, f"{-delta} jours de retard"))
                elif delta <= 30:
                    alertes_ct.append(("🟡 URGENT", v.immatriculation, v.marque+" "+v.modele, v.prochain_ct, f"dans {delta} jours"))
                elif delta <= 90:
                    alertes_ct.append(("🔵 BIENTÔT", v.immatriculation, v.marque+" "+v.modele, v.prochain_ct, f"dans {delta} jours"))
            except: pass

    # Vidanges
    for _, v in df_v.iterrows():
        if v.prochain_vidange and v.kilometrage:
            delta_km = int(v.prochain_vidange) - int(v.kilometrage)
            if delta_km <= 0:
                alertes_vid.append(("🔴 DÉPASSÉ", v.immatriculation, v.marque+" "+v.modele, int(v.kilometrage), int(v.prochain_vidange)))
            elif delta_km <= 500:
                alertes_vid.append(("🟡 URGENT", v.immatriculation, v.marque+" "+v.modele, int(v.kilometrage), int(v.prochain_vidange)))

    # Permis conducteurs
    for _, c in df_c.iterrows():
        if c.permis_expiration:
            try:
                exp = datetime.strptime(c.permis_expiration, "%Y-%m-%d").date()
                delta = (exp - today).days
                if delta < 0:
                    alertes_perm.append(("🔴 EXPIRÉ", c.nom+" "+c.prenom, c.service, c.permis_expiration))
                elif delta <= 60:
                    alertes_perm.append(("🟡 BIENTÔT", c.nom+" "+c.prenom, c.service, c.permis_expiration))
            except: pass

    # Maintenances planifiées
    df_m_plan = query("""
        SELECT m.*, v.immatriculation, v.marque||' '||v.modele AS vehicule
        FROM maintenances m JOIN vehicules v ON m.vehicule_id=v.id
        WHERE m.statut IN ('Planifiée','En cours')
    """)
    for _, m in df_m_plan.iterrows():
        alertes_maint.append((m.statut, m.immatriculation, m.vehicule, m.type_maintenance, m.date_intervention))

    nb_total = len(alertes_ct) + len(alertes_vid) + len(alertes_perm) + len(alertes_maint)
    if nb_total == 0:
        st.success("✅ Aucune alerte active. Parc automobile en bon état !")
    else:
        st.error(f"⚠️ **{nb_total} alerte(s) active(s)** — Action requise")

    if alertes_ct:
        st.markdown("### 🚦 Contrôles Techniques")
        df_ct = pd.DataFrame(alertes_ct, columns=["Niveau","Immat.","Véhicule","Date CT","Échéance"])
        st.dataframe(df_ct, use_container_width=True, hide_index=True)

    if alertes_vid:
        st.markdown("### 🔧 Vidanges")
        df_vd = pd.DataFrame(alertes_vid, columns=["Niveau","Immat.","Véhicule","Km actuel","Km vidange"])
        st.dataframe(df_vd, use_container_width=True, hide_index=True)

    if alertes_perm:
        st.markdown("### 📄 Permis Conducteurs")
        df_pm = pd.DataFrame(alertes_perm, columns=["Niveau","Conducteur","Service","Expiration"])
        st.dataframe(df_pm, use_container_width=True, hide_index=True)

    if alertes_maint:
        st.markdown("### 🛠️ Maintenances Planifiées / En cours")
        df_mp = pd.DataFrame(alertes_maint, columns=["Statut","Immat.","Véhicule","Type","Date prévue"])
        st.dataframe(df_mp, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding:1rem;text-align:center;
            border-top:1px solid #30363d;color:#8b949e;font-size:.8rem;
            font-family:'Rajdhani',sans-serif;letter-spacing:.06em;">
    FLEET MANAGER PRO · Base de données SQLite locale (<code>fleet_manager.db</code>)
    · Données sauvegardées automatiquement
</div>
""", unsafe_allow_html=True)
