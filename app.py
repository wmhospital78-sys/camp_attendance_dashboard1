# app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import io
from datetime import date

# Try to import AgGrid for a richer inline-edit experience; fallback available
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
    "primary": "#131321",   # sidebar color
    "card": "#1e1e2f",      # card color
    "accent": "#9b6bff",    # accent gradient color
    "bg": "#0f0f13",        # app background
    "text": "#EAEAEA"       # text color
}

# ensure settings exist
for k, v in DEFAULT_THEME.items():
    if load_setting(k) is None:
        save_setting(k, v)

# ---------------------------
# CSS builder using theme
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
    .sidebar-college {{
        font-weight: 700;
        font-size: 18px;
        color: {accent};
        text-align: center;
        margin-bottom: 6px;
    }}
    .sidebar-welcome {{
        text-align:center;
        color: {text};
        margin-bottom: 10px;
        font-weight:600;
    }}
    .dash-card {{
        background: {card};
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
        color: {text};
    }}
    .dash-card h3 {{
        margin: 0;
        font-size: 22px;
        font-weight:700;
    }}
    .dash-card p {{
        margin:0;
        color: #bdbdbd;
    }}
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
# UI - Sidebar & Header
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

    st.markdown("### PGs by Year")
    if not staff_df[staff_df["category"]=="PG"].empty:
        pg_counts = staff_df[staff_df["category"]=="PG"].groupby("pg_year").size().reset_index(name="count")
        fig2 = px.bar(pg_counts, x="pg_year", y="count", title="PGs by Year", text="count")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=load_setting('text', DEFAULT_THEME['text']))
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# PAGE: Add Staff
# ---------------------------
elif page == "Add Staff":
    st.subheader("➕ Add Staff (individual or Excel upload)")

    with st.form("add_staff_form"):
        serial_no = st.number_input("Serial Number", min_value=1, step=1)
        name = st.text_input("Name")
        category = st.selectbox("Category", ["Doctor", "Nurse", "Faculty", "PG", "Internee"])
        pg_year = st.selectbox("PG Year (if PG)", ["", "1st Year", "2nd Year", "3rd Year"]) if category=="PG" else ""
        joining_date = st.date_input("Joining Date", value=date.today())
        submitted = st.form_submit_button("Add Staff")
        if submitted:
            insert_staff(serial_no, name, category, pg_year, joining_date, 0)
            st.success(f"Added {name}")

    st.markdown("---")
    st.markdown("**Or upload Excel to bulk add / update**")
    uploaded = st.file_uploader("Upload Excel (.xlsx) containing staff columns", type=["xlsx"])
    if uploaded:
        df_in = pd.read_excel(uploaded)
        mode = st.radio("Import mode", options=["Append", "Replace existing"], index=0)
        replace = (mode == "Replace existing")
        import_staff_from_df(df_in, replace=replace)
        st.success("Excel imported into database.")

# ---------------------------
# PAGE: Manage Staff
# ---------------------------
elif page == "Manage Staff":
    st.subheader("👩‍⚕️ Manage Staff (edit / delete)")

    staff_df = fetch_staff_df()
    if staff_df.empty:
        st.info("No staff found. Add staff from 'Add Staff' or upload Excel.")
    else:
        st.markdown("""
            <style>
            .full-width-card {
                background: """ + load_setting('card', DEFAULT_THEME['card']) + """;
                padding: 16px;
                border-radius: 12px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.6);
                margin-bottom: 12px;
            }
            </style>
        """, unsafe_allow_html=True)

        if HAS_AGGRID:
            gb = GridOptionsBuilder.from_dataframe(staff_df)
            gb.configure_default_column(editable=True, resizable=True, sortable=True)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            gb.configure_pagination(paginationAutoPageSize=True)
            gridOptions = gb.build()

            st.markdown('<div class="full-width-card">', unsafe_allow_html=True)
            grid_response = AgGrid(
                staff_df,
                gridOptions=gridOptions,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                allow_unsafe_jscode=True,
                theme="dark",
                height=400
            )
            st.markdown('</div>', unsafe_allow_html=True)

            updated = pd.DataFrame(grid_response["data"])
            if st.button("💾 Save edits to database"):
                for _, r in updated.iterrows():
                    update_staff_row(r.to_dict())
                st.success("✅ Staff data updated.")

            sel = grid_response.get("selected_rows", [])
            if sel:
                sel_ids = [s["id"] for s in sel]
                if st.button("🗑️ Delete selected staff"):
                    for sid in sel_ids:
                        delete_staff_by_id(int(sid))
                    st.success(f"Deleted {len(sel_ids)} staff.")
                    update_camps_attended()
        else:
            edited = st.data_editor(staff_df, use_container_width=True)
            if st.button("💾 Save edits"):
                for _, r in edited.iterrows():
                    update_staff_row(r.to_dict())
                st.success("✅ Staff updated.")
            del_ids = st.multiselect("Select staff IDs to delete", staff_df["id"].tolist())
            if st.button("🗑️ Delete selected"):
                for sid in del_ids:
                    delete_staff_by_id(sid)
                st.success(f"Deleted {len(del_ids)} staff.")
                update_camps_attended()

# ---------------------------
# PAGE: Manage Camps
# ---------------------------
elif page == "Manage Camps":
    st.subheader("🏥 Manage Camps & Assignments")
    camps_df = fetch_camps_df()
    with st.form("add_camp"):
        title = st.text_input("Camp Title")
        camp_date = st.date_input("Camp Date", value=date.today())
        submitted = st.form_submit_button("Add Camp")
        if submitted:
            insert_camp(title, camp_date)
            st.success("Camp added.")

    st.markdown("### Existing camps")
    st.dataframe(camps_df, use_container_width=True)

    st.markdown("### Assign staff to a camp")
    camps_df = fetch_camps_df()
    staff_df = fetch_staff_df()
    if not camps_df.empty and not staff_df.empty:
        camp_choice = st.selectbox("Select camp", camps_df["title"].tolist())
        selected_camp_id = int(camps_df
