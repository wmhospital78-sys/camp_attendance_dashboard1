import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ----------------------------
# THEME COLORS
# ----------------------------
PRIMARY_COLOR = "#061F40"
SECONDARY_COLOR = "#051326"
ACCENT_COLOR = "#062540"
GRAY_COLOR = "#979DA6"
BG_COLOR = "#F2F2F2"

st.set_page_config(
    page_title="Camp Attendance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# SESSION STATE INIT
# ----------------------------
if "staff" not in st.session_state:
    st.session_state.staff = pd.DataFrame(columns=[
        "Serial Number", "Name", "Category", "PG Year", "Joining Date", "Camps Attended"
    ])

if "camps" not in st.session_state:
    st.session_state.camps = pd.DataFrame(columns=["Camp Title", "Date", "Assigned Staff"])

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def add_staff(serial, name, category, pg_year, joining_date, camps):
    new_row = {
        "Serial Number": serial,
        "Name": name,
        "Category": category,
        "PG Year": pg_year if category == "PG" else "",
        "Joining Date": joining_date,
        "Camps Attended": camps,
    }
    st.session_state.staff = pd.concat(
        [st.session_state.staff, pd.DataFrame([new_row])],
        ignore_index=True
    )

def delete_staff(index):
    st.session_state.staff = st.session_state.staff.drop(index).reset_index(drop=True)

def add_camp(title, date, staff_list):
    new_row = {
        "Camp Title": title,
        "Date": date,
        "Assigned Staff": ", ".join(staff_list)
    }
    st.session_state.camps = pd.concat(
        [st.session_state.camps, pd.DataFrame([new_row])],
        ignore_index=True
    )

# ----------------------------
# SIDEBAR NAVIGATION
# ----------------------------
st.sidebar.title("🏥 Navigation")
page = st.sidebar.radio("Go to", ["📊 Overview", "👩‍⚕️ Manage Staff", "🏥 Manage Camps", "📂 Export Data"])

# ----------------------------
# DASHBOARD OVERVIEW
# ----------------------------
if page == "📊 Overview":
    st.title("📊 Dashboard Overview")

    staff = st.session_state.staff

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Staff", len(staff))
    col2.metric("Doctors", (staff["Category"] == "Doctor").sum())
    col3.metric("Nursing Staff", (staff["Category"] == "Nurse").sum())
    col4.metric("Teaching Faculty", (staff["Category"] == "Faculty").sum())
    col5.metric("PGs", (staff["Category"] == "PG").sum())
    col6.metric("Internees", (staff["Category"] == "Internee").sum())

    # Pie chart: distribution
    if not staff.empty:
        fig_pie = px.pie(staff, names="Category", title="Staff Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)

        # PG bar chart
        pg_data = staff[staff["Category"] == "PG"]["PG Year"].value_counts().reset_index()
        pg_data.columns = ["PG Year", "Count"]
        if not pg_data.empty:
            fig_bar = px.bar(pg_data, x="PG Year", y="Count", title="PGs by Year")
            st.plotly_chart(fig_bar, use_container_width=True)

# ----------------------------
# MANAGE STAFF
# ----------------------------
elif page == "👩‍⚕️ Manage Staff":
    st.title("👩‍⚕️ Manage Staff")

    with st.form("add_staff_form", clear_on_submit=True):
        serial = st.text_input("Serial Number")
        name = st.text_input("Name")
        category = st.selectbox("Category", ["Doctor", "Nurse", "Faculty", "PG", "Internee"])
        pg_year = st.selectbox("PG Year", ["", "1st Year", "2nd Year", "3rd Year"]) if category == "PG" else ""
        joining_date = st.date_input("Joining Date")
        camps = st.number_input("Camps Attended", min_value=0, step=1)
        submitted = st.form_submit_button("➕ Add Staff")

        if submitted:
            add_staff(serial, name, category, pg_year, joining_date, camps)
            st.success(f"✅ {name} added successfully")

    st.subheader("📋 Staff Table")
    if not st.session_state.staff.empty:
        st.dataframe(st.session_state.staff, use_container_width=True)

        # Delete staff
        delete_index = st.number_input("Enter row index to delete", min_value=0,
                                       max_value=len(st.session_state.staff) - 1,
                                       step=1, key="del_idx")
        if st.button("🗑️ Delete Staff"):
            delete_staff(delete_index)
            st.success("✅ Staff deleted")

    # Excel upload
    st.subheader("⬆️ Upload Staff Excel")
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.session_state.staff = pd.concat([st.session_state.staff, df], ignore_index=True)
        st.success("✅ Excel data added successfully")

# ----------------------------
# MANAGE CAMPS
# ----------------------------
elif page == "🏥 Manage Camps":
    st.title("🏥 Manage Camps")

    with st.form("add_camp_form", clear_on_submit=True):
        title = st.text_input("Camp Title")
        date = st.date_input("Camp Date")
        staff_list = st.multiselect("Assign Staff", st.session_state.staff["Name"].tolist())
        submitted = st.form_submit_button("➕ Add Camp")
        if submitted:
            add_camp(title, date, staff_list)
            st.success(f"✅ Camp {title} added successfully")

    st.subheader("📋 Camps Table")
    st.dataframe(st.session_state.camps, use_container_width=True)

# ----------------------------
# EXPORT DATA
# ----------------------------
elif page == "📂 Export Data":
    st.title("📂 Export Data")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state.staff.to_excel(writer, index=False, sheet_name="Staff")
        st.session_state.camps.to_excel(writer, index=False, sheet_name="Camps")

    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name="staff_data_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
