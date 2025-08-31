import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ------------------ DATABASE ------------------
conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_no INTEGER,
    name TEXT,
    category TEXT,
    joining_date TEXT,
    pg_year TEXT,
    camps_attended INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS camps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS camp_assignments (
    camp_id INTEGER,
    staff_id INTEGER
)""")
conn.commit()

# ------------------ SESSION STATE ------------------
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"
if "custom_color" not in st.session_state:
    st.session_state.custom_color = "#131321"

# ------------------ THEME CSS ------------------
def apply_theme():
    if st.session_state.theme == "Dark":
        sidebar_bg = "#131321"
        text_color = "white"
    elif st.session_state.theme == "Light":
        sidebar_bg = "#ffffff"
        text_color = "#000000"
    else:
        sidebar_bg = st.session_state.custom_color
        text_color = "white"

    st.markdown(
        f"""
        <style>
            [data-testid="stSidebar"] {{
                background-color: {sidebar_bg};
                color: {text_color};
                box-shadow: 4px 0px 10px rgba(0,0,0,0.5);
            }}
            .sidebar-title {{
                font-size: 22px;
                font-weight: bold;
                padding: 10px;
                text-align: center;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_theme()

# ------------------ SIDEBAR ------------------
st.sidebar.markdown(
    "<div class='sidebar-title'>White Memorial Homoeo Medical College & Hospital</div>",
    unsafe_allow_html=True
)
st.sidebar.markdown("### 👋 Welcome Dr. Shabin S")

menu = st.sidebar.radio("Navigation", ["Overview", "Manage Staff", "Manage Camps", "Reports", "Settings"])

# ------------------ OVERVIEW ------------------
if menu == "Overview":
    st.title("📊 Dashboard Overview")

    staff_df = pd.read_sql("SELECT * FROM staff", conn)

    total = len(staff_df)
    doctors = len(staff_df[staff_df["category"] == "Doctor"])
    nurses = len(staff_df[staff_df["category"] == "Nurse"])
    faculty = len(staff_df[staff_df["category"] == "Faculty"])
    pgs = len(staff_df[staff_df["category"] == "PG"])
    internees = len(staff_df[staff_df["category"] == "Internee"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Staff", total)
    c2.metric("Doctors", doctors)
    c3.metric("Nurses", nurses)
    c4.metric("PGs", pgs)
    c5.metric("Internees", internees)

    if not staff_df.empty:
        pie = px.pie(staff_df, names="category", title="Staff Distribution")
        st.plotly_chart(pie, use_container_width=True)

        pg_df = staff_df[staff_df["category"] == "PG"]
        if not pg_df.empty:
            bar = px.bar(pg_df, x="pg_year", title="PGs by Year")
            st.plotly_chart(bar, use_container_width=True)

# ------------------ MANAGE STAFF ------------------
elif menu == "Manage Staff":
    st.title("👩‍⚕️ Manage Staff")

    with st.expander("➕ Add New Staff"):
        serial_no = st.number_input("Serial Number", min_value=1, step=1)
        name = st.text_input("Name")
        category = st.selectbox("Category", ["Doctor", "Nurse", "Faculty", "PG", "Internee"])
        joining_date = st.date_input("Joining Date")
        pg_year = st.selectbox("PG Year", ["NA", "1st Year", "2nd Year", "3rd Year"],
                               disabled=(category != "PG"))
        camps_attended = st.number_input("Camps Attended", min_value=0, step=1)
        if st.button("Add Staff"):
            c.execute("INSERT INTO staff (serial_no, name, category, joining_date, pg_year, camps_attended) VALUES (?,?,?,?,?,?)",
                      (serial_no, name, category, str(joining_date), pg_year, camps_attended))
            conn.commit()
            st.success("Staff added successfully!")

    staff_df = pd.read_sql("SELECT * FROM staff", conn)

    if not staff_df.empty:
        st.subheader("📋 Staff Records")

        gb = GridOptionsBuilder.from_dataframe(staff_df)
        gb.configure_pagination()
        gb.configure_default_column(editable=True)
        gb.configure_selection("single", use_checkbox=True)
        grid_options = gb.build()

        grid = AgGrid(
            staff_df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=True
        )

        selected = grid["selected_rows"]
        if selected:
            selected_id = selected[0]["id"]
            if st.button("Delete Selected"):
                c.execute("DELETE FROM staff WHERE id=?", (selected_id,))
                conn.commit()
                st.warning("Staff deleted!")

    st.subheader("⬆ Upload Staff from Excel")
    upload = st.file_uploader("Upload Excel", type=["xlsx"])
    if upload:
        df_new = pd.read_excel(upload)
        df_new.to_sql("staff", conn, if_exists="append", index=False)
        conn.commit()
        st.success("Uploaded successfully!")

# ------------------ MANAGE CAMPS ------------------
elif menu == "Manage Camps":
    st.title("🏥 Manage Camps")
    title = st.text_input("Camp Title")
    date = st.date_input("Camp Date")
    if st.button("Add Camp"):
        c.execute("INSERT INTO camps (title, date) VALUES (?,?)", (title, str(date)))
        conn.commit()
        st.success("Camp added!")

    st.subheader("Assign Staff to Camps")
    camps_df = pd.read_sql("SELECT * FROM camps", conn)
    staff_df = pd.read_sql("SELECT * FROM staff", conn)
    if not camps_df.empty and not staff_df.empty:
        camp_choice = st.selectbox("Select Camp", camps_df["title"])
        staff_choice = st.multiselect("Select Staff", staff_df["name"])
        if st.button("Assign"):
            camp_id = camps_df[camps_df["title"] == camp_choice]["id"].values[0]
            for s in staff_choice:
                staff_id = staff_df[staff_df["name"] == s]["id"].values[0]
                c.execute("INSERT INTO camp_assignments (camp_id, staff_id) VALUES (?,?)", (camp_id, staff_id))
            conn.commit()
            st.success("Assigned successfully!")

# ------------------ REPORTS ------------------
elif menu == "Reports":
    st.title("📂 Export Data")
    staff_df = pd.read_sql("SELECT * FROM staff", conn)
    camps_df = pd.read_sql("SELECT * FROM camps", conn)
    assign_df = pd.read_sql("SELECT * FROM camp_assignments", conn)

    with pd.ExcelWriter("staff_data_export.xlsx") as writer:
        staff_df.to_excel(writer, index=False, sheet_name="Staff")
        camps_df.to_excel(writer, index=False, sheet_name="Camps")
        assign_df.to_excel(writer, index=False, sheet_name="Assignments")

    with open("staff_data_export.xlsx", "rb") as f:
        st.download_button("Download Excel", f, file_name="staff_data_export.xlsx")

# ------------------ SETTINGS ------------------
elif menu == "Settings":
    st.title("⚙ Settings")
    theme = st.selectbox("Choose Theme", ["Dark", "Light", "Custom"], index=["Dark", "Light", "Custom"].index(st.session_state.theme))
    st.session_state.theme = theme
    if theme == "Custom":
        color = st.color_picker("Pick Sidebar Color", st.session_state.custom_color)
        st.session_state.custom_color = color
    apply_theme()
