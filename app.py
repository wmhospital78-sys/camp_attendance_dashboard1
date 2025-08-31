# app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import io
from datetime import date

# Try to import AgGrid for a richer inline-edit experience
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    HAS_AGGRID = True
except Exception:
    HAS_AGGRID = False

# ---------------------------
# DB & Initialization
# ---------------------------
DB_PATH = "camp_attendance.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        serial_no INTEGER,
        name TEXT,
        category TEXT,
        pg_year TEXT,
        joining_date TEXT,
        camps_attended INTEGER DEFAULT 0
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS camps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        camp_date TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camp_id INTEGER,
        staff_id INTEGER,
        FOREIGN KEY(camp_id) REFERENCES camps(id),
        FOREIGN KEY(staff_id) REFERENCES staff(id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# Settings helpers
# ---------------------------
def save_setting(key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def load_setting(key, default=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

# default theme
DEFAULT_THEME = {
    "primary": "#131321",
    "card": "#1e1e2f",
    "accent": "#9b6bff",
    "bg": "#0f0f13",
    "text": "#EAEAEA"
}

for k, v in DEFAULT_THEME.items():
    if load_setting(k) is None:
        save_setting(k, v)

# ---------------------------
# CSS builder
# ---------------------------
def render_css():
    primary = load_setting("primary", DEFAULT_THEME["primary"])
    card = load_setting("card", DEFAULT_THEME["card"])
    accent = load_setting("accent", DEFAULT_THEME["accent"])
    bg = load_setting("bg", DEFAULT_THEME["bg"])
    text = load_setting("text", DEFAULT_THEME["text"])

    css = f"""
    <style>
    .stApp {{
        background: {bg};
        color: {text};
    }}
    section[data-testid="stSidebar"] {{
        background: {primary} !important;
        color: {text} !important;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 6px 0 30px rgba(0,0,0,0.6);
    }}
    .dash-card {{
        background: {card};
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
        color: {text};
        margin-bottom:12px;
    }}
    .dash-card h3 {{ margin:0;font-size:22px;font-weight:700; }}
    .dash-card p {{ margin:0;color:#bdbdbd; }}
    div.stButton>button {{
        background: linear-gradient(90deg, {accent}, #6d3cff) !important;
        color: white;
        border-radius: 10px;
        padding: 8px 14px;
        font-weight:700;
    }}
    div.stButton>button:hover {{
        box-shadow: 0 6px 20px rgba(107, 63, 255, 0.25);
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

render_css()

# ---------------------------
# DB CRUD helpers
# ---------------------------
def fetch_staff_df():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM staff ORDER BY COALESCE(serial_no, id)", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["id","serial_no","name","category","pg_year","joining_date","camps_attended"])
    return df

def insert_staff(serial_no, name, category, pg_year, joining_date, camps_attended):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO staff(serial_no, name, category, pg_year, joining_date, camps_attended) VALUES (?, ?, ?, ?, ?, ?)",
        (serial_no, name, category, pg_year, str(joining_date), camps_attended)
    )
    conn.commit()
    conn.close()

def update_staff_row(row: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE staff SET serial_no=?, name=?, category=?, pg_year=?, joining_date=?, camps_attended=? WHERE id=?
    """, (row.get("serial_no"), row.get("name"), row.get("category"), row.get("pg_year"), row.get("joining_date"), row.get("camps_attended"), row.get("id")))
    conn.commit()
    conn.close()

def delete_staff_by_id(id_):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM staff WHERE id=?", (id_,))
    conn.commit()
    conn.close()

def import_staff_from_df(df: pd.DataFrame, replace=False):
    conn = get_conn()
    if replace:
        conn.execute("DELETE FROM staff")
    df = df.copy()
    expected = ["serial_no","name","category","pg_year","joining_date","camps_attended"]
    col_map = {}
    for col in df.columns:
        lc = col.strip().lower()
        if "serial" in lc or "sl" in lc:
            col_map[col] = "serial_no"
        elif "name" in lc:
            col_map[col] = "name"
        elif "category" in lc:
            col_map[col] = "category"
        elif "pg" in lc or "year" in lc:
            col_map[col] = "pg_year"
        elif "join" in lc or "joining" in lc or "doj" in lc:
            col_map[col] = "joining_date"
        elif "camp" in lc or "attend" in lc:
            col_map[col] = "camps_attended"
    df = df.rename(columns=col_map)
    for e in expected:
        if e not in df.columns:
            df[e] = None
    df = df[expected].fillna({"camps_attended":0})
    df.to_sql("staff", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

# Camps helpers
def fetch_camps_df():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM camps ORDER BY camp_date DESC", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["id","title","camp_date"])
    return df

def insert_camp(title, camp_date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO camps(title, camp_date) VALUES (?, ?)", (title, str(camp_date)))
    conn.commit()
    conn.close()

def fetch_assignments():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT a.id as assign_id, c.title as camp_title, s.name as staff_name, a.camp_id, a.staff_id
        FROM assignments a
        JOIN camps c ON c.id=a.camp_id
        JOIN staff s ON s.id=a.staff_id
        ORDER BY c.camp_date DESC
    """, conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["assign_id","camp_title","staff_name","camp_id","staff_id"])
    return df

def assign_staff(camp_id, staff_ids):
    conn = get_conn()
    cur = conn.cursor()
    for sid in staff_ids:
        cur.execute("INSERT OR IGNORE INTO assignments(camp_id, staff_id) VALUES (?, ?)", (camp_id, sid))
    conn.commit()
    conn.close()
    update_camps_attended()

def update_camps_attended():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE staff SET camps_attended = 0")
    cur.execute("""
        UPDATE staff
        SET camps_attended = (
            SELECT COUNT(*) FROM assignments WHERE staff_id = staff.id
        )
    """)
    conn.commit()
    conn.close()

# ---------------------------
# Sidebar & Header
# ---------------------------
st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between">
      <div>
        <h1 style="margin:6px 0 2px 0;color:{load_setting('accent', DEFAULT_THEME['accent'])};">
          White Memorial Homoeopathic Medical College & Hospital
        </h1>
        <div style="color:#cfcfcf;font-weight:600;margin-bottom:6px">Overview</div>
      </div>
      <div style="text-align:right;">
        <div style="font-weight:700;color:{load_setting('text', DEFAULT_THEME['text'])}">Welcome, Dr. Shabin S</div>
        <div style="color:#a0a0a0;font-size:13px">Hospital Admin</div>
      </div>
    </div>
    <hr style="opacity:0.15"/>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"<div style='padding:8px 6px; color:{load_setting('text')}'>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigate", ["Dashboard", "Add Staff", "Manage Staff", "Manage Camps", "Reports", "Settings"])
st.sidebar.markdown("</div>", unsafe_allow_html=True)
render_css()

# ---------------------------
# PAGE: Dashboard
# ---------------------------
if page == "Dashboard":
    st.subheader("📊 Overview")
    staff_df = fetch_staff_df()
    camps_df = fetch_camps_df()

    total_staff = len(staff_df)
    doctors = len(staff_df[staff_df["category"] == "Doctor"])
    nursing = len(staff_df[staff_df["category"] == "Nurse"])
    faculty = len(staff_df[staff_df["category"] == "Faculty"])
    pgs = len(staff_df[staff_df["category"] == "PG"])
    internees = len(staff_df[staff_df["category"] == "Internee"])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f"<div class='dash-card'><h3>{total_staff}</h3><p>Total Staff</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='dash-card'><h3>{doctors}</h3><p>Doctors</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='dash-card'><h3>{nursing}</h3><p>Nursing Staff</p></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='dash-card'><h3>{faculty}</h3><p>Teaching Faculty</p></div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='dash-card'><h3>{pgs}</h3><p>PGs</p></div>", unsafe_allow_html=True)
    c6.markdown(f"<div class='dash-card'><h3>{internees}</h3><p>Internees</p></div>", unsafe_allow_html=True)

    st.markdown("### Staff Distribution")
    if not staff_df.empty:
        fig = px.pie(staff_df, names="category", title="Staff Distribution by Category",
                     color_discrete_sequence=px.colors.sequential.Plasma)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=load_setting('text', DEFAULT_THEME['text']))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### PGs by Year
