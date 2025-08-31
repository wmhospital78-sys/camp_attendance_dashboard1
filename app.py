# app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import io
import os
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

# default theme (can be changed in Settings)
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
    /* App background & text */
    .stApp {{
        background: {bg};
        color: {text};
    }}
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {primary} !important;
        color: {text} !important;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 6px 0 30px rgba(0,0,0,0.6);
    }}
    section[data-testid="stSidebar"] .css-1d391kg {{
        background: transparent;
    }}
    /* Sidebar headings */
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
    /* Cards */
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
    /* Buttons */
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

# render CSS once
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
    # ensure columns exist; map expected names
    expected = ["serial_no","name","category","pg_year","joining_date","camps_attended"]
    # try several alternatives for column names
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
    # fill missing expected columns
    for e in expected:
        if e not in df.columns:
            df[e] = None
    df = df[expected]
    df = df.fillna({"camps_attended":0})
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
        # avoid duplicates
        cur.execute("INSERT OR IGNORE INTO assignments(camp_id, staff_id) VALUES (?, ?)", (camp_id, sid))
    conn.commit()
    conn.close()

# ---------------------------
# UI - Sidebar & Header
# ---------------------------
st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)  # spacing
# Big college name on top of page (outside sidebar per user's request)
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

# Sidebar navigation (modern styled)
st.sidebar.markdown(f"<div style='padding:8px 6px; color:{load_setting('text')}'>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigate", ["Dashboard", "Add Staff", "Manage Staff", "Manage Camps", "Reports", "Settings"])
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# render CSS again if theme changed
render_css()

# ---------------------------
# PAGE: Dashboard
# ---------------------------
if page == "Dashboard":
    st.subheader("📊 Overview")

    staff_df = fetch_staff_df()
    camps_df = fetch_camps_df()

    # Metrics
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
    uploaded = st.file_uploader("Upload Excel (.xlsx) containing staff columns (Serial/Name/Category/PG Year/Joining Date/Camps Attended)", type=["xlsx"])
    if uploaded:
        df_in = pd.read_excel(uploaded)
        # Ask whether to replace or append
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
        if HAS_AGGRID:
            gb = GridOptionsBuilder.from_dataframe(staff_df)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_default_column(editable=True)
            gb.configure_selection(selection_mode="single", use_checkbox=True)
            gridOptions = gb.build()
            grid_response = AgGrid(staff_df, gridOptions=gridOptions, update_mode=GridUpdateMode.MODEL_CHANGED, allow_unsafe_jscode=True, theme="dark", height=360)
            updated = pd.DataFrame(grid_response["data"])
            # Save edits button
            if st.button("Save changes to database"):
                # iterate rows and update
                for _, r in updated.iterrows():
                    update_staff_row(r.to_dict())
                st.success("Updated database with edits.")
            # delete selected
            sel = grid_response.get("selected_rows", [])
            if sel:
                sid = sel[0].get("id")
                if st.button("Delete selected staff"):
                    delete_staff_by_id(int(sid))
                    st.success("Deleted staff.")
        else:
            # fallback to data_editor
            edited = st.data_editor(staff_df, use_container_width=True)
            if st.button("Save edits"):
                # apply row by row update
                for _, r in edited.iterrows():
                    update_staff_row(r.to_dict())
                st.success("Saved edits to DB.")
            # delete by id
            del_id = st.number_input("Enter staff ID to delete", min_value=0, step=1)
            if st.button("Delete by ID"):
                delete_staff_by_id(int(del_id))
                st.success("Deleted staff id " + str(del_id))

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
        selected_camp_id = int(camps_df[camps_df["title"]==camp_choice]["id"].iloc[0])
        staff_map = staff_df.set_index("id")["name"].to_dict()
        picks = st.multiselect("Select staff", options=list(staff_map.values()))
        pick_ids = [int(k) for k,v in staff_map.items() if v in picks]
        if st.button("Assign selected to camp"):
            assign_staff(selected_camp_id, pick_ids)
            st.success("Assigned staff to camp.")
    else:
        st.info("Add camps and staff first.")

    st.markdown("### Current Assignments")
    st.dataframe(fetch_assignments(), use_container_width=True)

# ---------------------------
# PAGE: Reports
# ---------------------------
elif page == "Reports":
    st.subheader("📈 Reports & Exports")
    staff_df = fetch_staff_df()
    camps_df = fetch_camps_df()
    assignments_df = fetch_assignments()

    st.markdown("#### Quick stats")
    st.write("Total staff:", len(staff_df))
    st.write("Total camps:", len(camps_df))

    st.markdown("#### Export full dataset to Excel")
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        staff_df.to_excel(writer, index=False, sheet_name="Staff")
        camps_df.to_excel(writer, index=False, sheet_name="Camps")
        assignments_df.to_excel(writer, index=False, sheet_name="Assignments")
    st.download_button("Download staff_data_export.xlsx", out.getvalue(), file_name="staff_data_export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("#### Attendance overview")
    if not staff_df.empty:
        fig = px.histogram(staff_df, x="camps_attended", nbins=20, title="Camps Attended Distribution")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=load_setting('text', DEFAULT_THEME['text']))
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# PAGE: Settings
# ---------------------------
elif page == "Settings":
    st.subheader("⚙️ Settings - Theme & App")
    st.markdown("Change app colors. These are saved and applied immediately.")

    primary = st.color_picker("Sidebar color (Primary)", value=load_setting("primary", DEFAULT_THEME["primary"]))
    card = st.color_picker("Card background color", value=load_setting("card", DEFAULT_THEME["card"]))
    accent = st.color_picker("Accent / Gradient color", value=load_setting("accent", DEFAULT_THEME["accent"]))
    bg = st.color_picker("App background color", value=load_setting("bg", DEFAULT_THEME["bg"]))
    textc = st.color_picker("Main text color", value=load_setting("text", DEFAULT_THEME["text"]))

    if st.button("Save Theme"):
        save_setting("primary", primary)
        save_setting("card", card)
        save_setting("accent", accent)
        save_setting("bg", bg)
        save_setting("text", textc)
        st.success("Theme saved — re-rendering styles.")
        render_css()

    st.markdown("#### Reset data (danger zone)")
    if st.button("Reset ALL data (staff, camps, assignments)"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM staff")
        cur.execute("DELETE FROM camps")
        cur.execute("DELETE FROM assignments")
        conn.commit()
        conn.close()
        st.success("All data cleared.")
