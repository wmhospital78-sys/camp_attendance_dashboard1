import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("staff_data.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_no INTEGER,
    name TEXT,
    category TEXT,
    pg_year TEXT,
    joining_date TEXT,
    camps_attended INTEGER
)''')

c.execute('''CREATE TABLE IF NOT EXISTS camps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS camp_assignments (
    camp_id INTEGER,
    staff_id INTEGER,
    FOREIGN KEY(camp_id) REFERENCES camps(id),
    FOREIGN KEY(staff_id) REFERENCES staff(id)
)''')
conn.commit()

# -----------------------------
# CUSTOM CSS FOR MODERN UI
# -----------------------------
st.markdown("""
    <style>
    /* Global background */
    .stApp {
        background-color: #131321;
        color: #EAEAEA;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a1a1d;
        box-shadow: 2px 0px 15px rgba(0,0,0,0.7);
    }
    section[data-testid="stSidebar"] .css-1d391kg {
        background-color: transparent;
    }

    /* Cards */
    .card {
        background: rgba(255,255,255,0.05);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }

    .card h3 {
        font-size: 22px;
        font-weight: 600;
        color: #fff;
    }

    .stat-number {
        font-size: 28px;
        font-weight: bold;
        background: linear-gradient(90deg, #9c27b0, #e040fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Buttons */
    div.stButton>button {
        background: linear-gradient(90deg, #9c27b0, #e040fb);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton>button:hover {
        box-shadow: 0px 0px 15px #e040fb;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def fetch_staff():
    return pd.read_sql("SELECT * FROM staff", conn)

def fetch_camps():
    return pd.read_sql("SELECT * FROM camps", conn)

# -----------------------------
# SIDEBAR MENU
# -----------------------------
menu = ["🏠 Dashboard", "👩‍⚕️ Manage Staff", "🏥 Manage Camps", "📂 Export Data"]
choice = st.sidebar.radio("Navigation", menu)

# -----------------------------
# DASHBOARD
# -----------------------------
if choice == "🏠 Dashboard":
    st.markdown("<h2 style='color:white;'>📊 Staff Overview</h2>", unsafe_allow_html=True)

    df = fetch_staff()

    if df.empty:
        st.info("No staff records found. Please add staff in 'Manage Staff'.")
    else:
        total_staff = len(df)
        doctors = len(df[df["category"] == "Doctor"])
        nurses = len(df[df["category"] == "Nurse"])
        faculty = len(df[df["category"] == "Faculty"])
        pgs = len(df[df["category"] == "PG"])
        internees = len(df[df["category"] == "Internee"])

        # Cards Layout
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f"<div class='card'><h3>Total Staff</h3><p class='stat-number'>{total_staff}</p></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='card'><h3>Doctors</h3><p class='stat-number'>{doctors}</p></div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='card'><h3>Nursing Staff</h3><p class='stat-number'>{nurses}</p></div>", unsafe_allow_html=True)

        col4, col5 = st.columns(2)
        with col4: st.markdown(f"<div class='card'><h3>Faculty</h3><p class='stat-number'>{faculty}</p></div>", unsafe_allow_html=True)
        with col5: st.markdown(f"<div class='card'><h3>Internees</h3><p class='stat-number'>{internees}</p></div>", unsafe_allow_html=True)

        # Pie chart
        fig = px.pie(df, names="category", title="Staff Distribution", color_discrete_sequence=px.colors.sequential.Plasma)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# MANAGE STAFF
# -----------------------------
elif choice == "👩‍⚕️ Manage Staff":
    st.markdown("<h2 style='color:white;'>👩‍⚕️ Manage Staff</h2>", unsafe_allow_html=True)

    with st.form("staff_form", clear_on_submit=True):
        serial_no = st.number_input("Serial Number", min_value=1)
        name = st.text_input("Name")
        category = st.selectbox("Category", ["Doctor", "Nurse", "Faculty", "PG", "Internee"])
        pg_year = st.text_input("PG Year (if applicable)")
        joining_date = st.date_input("Joining Date")
        camps_attended = st.number_input("Camps Attended", min_value=0)

        submitted = st.form_submit_button("➕ Add Staff")
        if submitted:
            c.execute("INSERT INTO staff (serial_no, name, category, pg_year, joining_date, camps_attended) VALUES (?,?,?,?,?,?)",
                      (serial_no, name, category, pg_year, str(joining_date), camps_attended))
            conn.commit()
            st.success(f"Staff {name} added!")

    df = fetch_staff()
    if not df.empty:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=True, groupable=True)
        gb.configure_selection('single', use_checkbox=True)
        gridOptions = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            theme="alpine",
            height=300,
            fit_columns_on_grid_load=True,
        )

        updated = grid_response["data"]
        if not updated.equals(df):
            updated.to_sql("staff", conn, if_exists="replace", index=False)
            st.success("Staff table updated!")

# -----------------------------
# EXPORT DATA
# -----------------------------
elif choice == "📂 Export Data":
    st.markdown("<h2 style='color:white;'>📂 Export Data</h2>", unsafe_allow_html=True)
    df_staff = fetch_staff()
    df_camps = fetch_camps()

    with pd.ExcelWriter("staff_data_export.xlsx") as writer:
        df_staff.to_excel(writer, index=False, sheet_name="Staff")
        df_camps.to_excel(writer, index=False, sheet_name="Camps")

    with open("staff_data_export.xlsx", "rb") as f:
        st.download_button("⬇ Download Excel", f, "staff_data_export.xlsx")
