import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import io
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# =============================
# DATABASE SETUP
# =============================
conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor()

# Staff Table
c.execute("""
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_no INTEGER,
    name TEXT,
    category TEXT,
    joining_date TEXT,
    pg_year TEXT,
    camps_attended INTEGER
)
""")

# Camps Table
c.execute("""
CREATE TABLE IF NOT EXISTS camps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    camp_date TEXT
)
""")

# Assignments Table
c.execute("""
CREATE TABLE IF NOT EXISTS camp_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camp_id INTEGER,
    staff_id INTEGER,
    FOREIGN KEY (camp_id) REFERENCES camps(id),
    FOREIGN KEY (staff_id) REFERENCES staff(id)
)
""")
conn.commit()


# =============================
# HELPER FUNCTIONS
# =============================
def get_staff():
    return pd.read_sql("SELECT * FROM staff", conn)

def get_camps():
    return pd.read_sql("SELECT * FROM camps", conn)

def add_staff(serial_no, name, category, joining_date, pg_year, camps_attended):
    c.execute("INSERT INTO staff (serial_no, name, category, joining_date, pg_year, camps_attended) VALUES (?, ?, ?, ?, ?, ?)",
              (serial_no, name, category, joining_date, pg_year, camps_attended))
    conn.commit()

def delete_staff(staff_id):
    c.execute("DELETE FROM staff WHERE id=?", (staff_id,))
    conn.commit()

def update_staff(staff_df):
    c.execute("DELETE FROM staff")  # Clear
    conn.commit()
    staff_df.to_sql("staff", conn, if_exists="append", index=False)


def add_camp(title, camp_date):
    c.execute("INSERT INTO camps (title, camp_date) VALUES (?, ?)", (title, camp_date))
    conn.commit()

def assign_staff_to_camp(camp_id, staff_ids):
    for sid in staff_ids:
        c.execute("INSERT INTO camp_assignments (camp_id, staff_id) VALUES (?, ?)", (camp_id, sid))
    conn.commit()

# =============================
# CUSTOM CSS FOR MODERN LOOK
# =============================
st.markdown("""
<style>
/* Dark Sidebar */
[data-testid="stSidebar"] {
    background-color: #131321 !important;
    color: white !important;
    box-shadow: 2px 0px 15px rgba(0,0,0,0.6);
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: white !important;
    font-weight: 500;
}

/* Dashboard Cards */
.card {
    background: #1e1e2f;
    color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    text-align: center;
}
.card h3 {
    margin: 0;
    font-size: 24px;
}
.card p {
    font-size: 18px;
    opacity: 0.8;
}
</style>
""", unsafe_allow_html=True)


# =============================
# SIDEBAR NAVIGATION
# =============================
st.sidebar.title("🏥 Hospital Dashboard")
menu = st.sidebar.radio("Navigate", ["📊 Overview", "👩‍⚕️ Manage Staff", "🏥 Manage Camps", "📂 Export Data"])

# =============================
# OVERVIEW
# =============================
if menu == "📊 Overview":
    st.title("📊 Dashboard Overview")

    staff_df = get_staff()

    total_staff = len(staff_df)
    doctors = len(staff_df[staff_df['category']=="Doctor"])
    nurses = len(staff_df[staff_df['category']=="Nurse"])
    faculty = len(staff_df[staff_df['category']=="Faculty"])
    pgs = len(staff_df[staff_df['category']=="PG"])
    internees = len(staff_df[staff_df['category']=="Internee"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card'><h3>{total_staff}</h3><p>Total Staff</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><h3>{doctors}</h3><p>Doctors</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'><h3>{nurses}</h3><p>Nursing Staff</p></div>", unsafe_allow_html=True)

    col4, col5 = st.columns(2)
    with col4:
        st.markdown(f"<div class='card'><h3>{faculty}</h3><p>Teaching Faculty</p></div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='card'><h3>{pgs}</h3><p>PGs</p></div>", unsafe_allow_html=True)

    st.markdown(f"<div class='card'><h3>{internees}</h3><p>Internees</p></div>", unsafe_allow_html=True)

    # Pie Chart
    if not staff_df.empty:
        fig = px.pie(staff_df, names="category", title="Staff Distribution by Category")
        st.plotly_chart(fig, use_container_width=True)

        pg_df = staff_df[staff_df["category"]=="PG"]
        if not pg_df.empty:
            fig2 = px.bar(pg_df, x="pg_year", title="PGs by Year")
            st.plotly_chart(fig2, use_container_width=True)


# =============================
# MANAGE STAFF
# =============================
elif menu == "👩‍⚕️ Manage Staff":
    st.title("👩‍⚕️ Manage Staff")

    with st.form("add_staff_form"):
        col1, col2 = st.columns(2)
        with col1:
            serial_no = st.number_input("Serial Number", min_value=1, step=1)
            name = st.text_input("Name")
            category = st.selectbox("Category", ["Doctor", "Nurse", "Faculty", "PG", "Internee"])
        with col2:
            joining_date = st.date_input("Joining Date")
            pg_year = st.selectbox("PG Year", ["NA", "1st Year", "2nd Year", "3rd Year"]) if category=="PG" else "NA"
            camps_attended = st.number_input("Camps Attended", min_value=0, step=1)

        submitted = st.form_submit_button("➕ Add Staff")
        if submitted and name:
            add_staff(serial_no, name, category, str(joining_date), pg_year, camps_attended)
            st.success("✅ Staff Added!")

    staff_df = get_staff()

    if not staff_df.empty:
        st.subheader("📋 Staff Records (Editable Table)")
        gb = GridOptionsBuilder.from_dataframe(staff_df)
        gb.configure_pagination()
        gb.configure_side_bar()
        gb.configure_default_column(editable=True)
        gb.configure_selection('single', use_checkbox=True)
        grid_options = gb.build()

        grid = AgGrid(
            staff_df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            allow_unsafe_jscode=True,
            theme="alpine"
        )

        if st.button("💾 Save Changes"):
            new_df = grid["data"]
            update_staff(pd.DataFrame(new_df))
            st.success("✅ Staff Updated!")

        if grid["selected_rows"]:
            selected_id = grid["selected_rows"][0]["id"]
            if st.button("🗑 Delete Selected"):
                delete_staff(selected_id)
                st.warning("❌ Staff Deleted!")


    uploaded_file = st.file_uploader("⬆ Upload Excel to Replace Staff Data", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        update_staff(df)
        st.success("✅ Staff Data Replaced with Excel Upload!")


# =============================
# MANAGE CAMPS
# =============================
elif menu == "🏥 Manage Camps":
    st.title("🏥 Manage Camps")

    with st.form("add_camp_form"):
        title = st.text_input("Camp Title")
        camp_date = st.date_input("Camp Date")
        submitted = st.form_submit_button("➕ Add Camp")
        if submitted and title:
            add_camp(title, str(camp_date))
            st.success("✅ Camp Added!")

    camps_df = get_camps()
    st.dataframe(camps_df)


# =============================
# EXPORT DATA
# =============================
elif menu == "📂 Export Data":
    st.title("📂 Export All Data")

    staff_df = get_staff()
    camps_df = get_camps()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        staff_df.to_excel(writer, index=False, sheet_name="Staff")
        camps_df.to_excel(writer, index=False, sheet_name="Camps")

    st.download_button(
        label="⬇ Download All Data as Excel",
        data=output.getvalue(),
        file_name="hospital_data_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
