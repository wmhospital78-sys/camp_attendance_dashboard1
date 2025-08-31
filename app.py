import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from io import BytesIO

# -------------------- DATABASE --------------------
conn = sqlite3.connect("staff_camps.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_no INTEGER,
    name TEXT,
    category TEXT,
    pg_year TEXT,
    joining_date TEXT,
    camps_attended INTEGER DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS camps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS camp_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camp_id INTEGER,
    staff_id INTEGER,
    FOREIGN KEY (camp_id) REFERENCES camps(id),
    FOREIGN KEY (staff_id) REFERENCES staff(id)
)''')

conn.commit()

# -------------------- HELPER FUNCTIONS --------------------
def load_staff():
    return pd.read_sql("SELECT * FROM staff", conn)

def load_camps():
    return pd.read_sql("SELECT * FROM camps", conn)

def save_staff(df):
    c.execute("DELETE FROM staff")
    df.to_sql("staff", conn, if_exists="append", index=False)
    conn.commit()

# -------------------- SIDEBAR DESIGN --------------------
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #061F40;
    }
    [data-testid="stSidebar"] * {
        color: #F2F2F2 !important;
    }
    .css-1d391kg {
        background-color: #F2F2F2;
    }
    .dashboard-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------- NAVIGATION --------------------
st.sidebar.title("🏥 Dashboard Menu")
page = st.sidebar.radio("Navigate", ["📊 Overview", "👩‍⚕️ Manage Staff", "🏥 Manage Camps", "📂 Export/Import"])

# -------------------- OVERVIEW --------------------
if page == "📊 Overview":
    st.title("Hospital Staff & Camp Dashboard")

    staff_df = load_staff()
    camps_df = load_camps()

    total_staff = len(staff_df)
    doctors = len(staff_df[staff_df["category"] == "Doctor"])
    nurses = len(staff_df[staff_df["category"] == "Nurse"])
    faculty = len(staff_df[staff_df["category"] == "Faculty"])
    pgs = len(staff_df[staff_df["category"] == "PG"])
    internees = len(staff_df[staff_df["category"] == "Internee"])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown(f"<div class='dashboard-card'><h3>{total_staff}</h3><p>Total Staff</p></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='dashboard-card'><h3>{doctors}</h3><p>Doctors</p></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='dashboard-card'><h3>{nurses}</h3><p>Nursing Staff</p></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='dashboard-card'><h3>{faculty}</h3><p>Faculty</p></div>", unsafe_allow_html=True)
    col5.markdown(f"<div class='dashboard-card'><h3>{pgs}</h3><p>PGs</p></div>", unsafe_allow_html=True)

    # Pie Chart - Staff Distribution
    if not staff_df.empty:
        fig = px.pie(staff_df, names="category", title="Staff Distribution")
        st.plotly_chart(fig)

    # PG Year Distribution
    pg_df = staff_df[staff_df["category"] == "PG"]
    if not pg_df.empty:
        fig2 = px.bar(pg_df, x="pg_year", title="PGs by Year")
        st.plotly_chart(fig2)

# -------------------- MANAGE STAFF --------------------
elif page == "👩‍⚕️ Manage Staff":
    st.title("Manage Staff Records")

    staff_df = load_staff()

    gb = GridOptionsBuilder.from_dataframe(staff_df)
    gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_default_column(editable=True, groupable=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        staff_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True
    )

    updated_df = grid_response['data']

    if st.button("💾 Save Changes"):
        save_staff(updated_df)
        st.success("Staff data updated successfully!")

    st.subheader("📤 Upload Staff via Excel")
    uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
    if uploaded:
        df_new = pd.read_excel(uploaded)
        save_staff(df_new)
        st.success("Staff uploaded & saved to database!")

# -------------------- MANAGE CAMPS --------------------
elif page == "🏥 Manage Camps":
    st.title("Manage Camps")

    camps_df = load_camps()
    st.dataframe(camps_df)

    with st.form("AddCamp"):
        title = st.text_input("Camp Title")
        date = st.date_input("Camp Date")
        submit = st.form_submit_button("➕ Add Camp")
        if submit:
            c.execute("INSERT INTO camps (title, date) VALUES (?, ?)", (title, str(date)))
            conn.commit()
            st.success("Camp added successfully!")

# -------------------- EXPORT/IMPORT --------------------
elif page == "📂 Export/Import":
    st.title("Export & Import Data")

    staff_df = load_staff()
    camps_df = load_camps()

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        staff_df.to_excel(writer, index=False, sheet_name="Staff")
        camps_df.to_excel(writer, index=False, sheet_name="Camps")

    st.download_button("⬇ Download Full Data", output.getvalue(), "staff_data_export.xlsx")

