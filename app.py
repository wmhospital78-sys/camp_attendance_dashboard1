import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Hospital Camp Dashboard", layout="wide")

# ===============================
# Header
# ===============================
st.markdown(
    """
    <h1 style='text-align:center; color:#2E86C1;'>🏥 White Memorial Homoeopathic Medical College & Hospital</h1>
    <h3 style='text-align:center;'>Camp Attendance & Staff Management Dashboard</h3>
    <hr>
    """,
    unsafe_allow_html=True
)

# ===============================
# Session State Initialization
# ===============================
if "staff" not in st.session_state:
    st.session_state.staff = pd.DataFrame([
        {"Serial No": 1, "Name": "Dr. A Kumar", "Category": "Doctor", "PG Year": None, "Joining Date": "2021-06-15"},
        {"Serial No": 2, "Name": "Nurse B Devi", "Category": "Nurse", "PG Year": None, "Joining Date": "2022-01-20"},
        {"Serial No": 3, "Name": "PG Student C", "Category": "PG", "PG Year": "Year 1", "Joining Date": "2023-07-10"},
    ])

if "camps" not in st.session_state:
    st.session_state.camps = pd.DataFrame(columns=["Title", "Camp Date"])

if "camp_assignments" not in st.session_state:
    st.session_state.camp_assignments = pd.DataFrame(columns=["Camp", "Staff"])

# ===============================
# Dashboard Overview
# ===============================
st.subheader("📊 Dashboard Overview")

staff = st.session_state.staff
total_staff = len(staff)
doctors = len(staff[staff["Category"] == "Doctor"])
nurses = len(staff[staff["Category"] == "Nurse"])
faculty = len(staff[staff["Category"] == "Faculty"])
pgs = len(staff[staff["Category"] == "PG"])
internees = len(staff[staff["Category"] == "Internee"])

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Staff", total_staff)
col2.metric("Doctors", doctors)
col3.metric("Nursing Staff", nurses)
col4.metric("Faculty", faculty)
col5.metric("PGs", pgs)
col6.metric("Internees", internees)

# Pie Chart
pie_fig = px.pie(
    staff, names="Category", title="Staff Distribution by Category"
)
st.plotly_chart(pie_fig, use_container_width=True)

# Bar Chart for PGs
pg_split = staff[staff["Category"] == "PG"]["PG Year"].value_counts().reset_index()
pg_split.columns = ["PG Year", "Count"]

if not pg_split.empty:
    bar_fig = px.bar(pg_split, x="PG Year", y="Count", title="PGs by Year")
    st.plotly_chart(bar_fig, use_container_width=True)

# ===============================
# Manage Staff
# ===============================
st.subheader("👩‍⚕️ Manage Staff")

with st.expander("➕ Add / Edit Staff"):
    serial = len(staff) + 1
    name = st.text_input("Name")
    category = st.selectbox("Category", ["Doctor", "Nurse", "Faculty", "PG", "Internee"])
    pg_year = None
    if category == "PG":
        pg_year = st.selectbox("PG Year", ["Year 1", "Year 2", "Year 3"])
    joining_date = st.date_input("Joining Date")

    if st.button("Add Staff"):
        new_row = {
            "Serial No": serial,
            "Name": name,
            "Category": category,
            "PG Year": pg_year,
            "Joining Date": joining_date.strftime("%Y-%m-%d")
        }
        st.session_state.staff = pd.concat([st.session_state.staff, pd.DataFrame([new_row])], ignore_index=True)
        st.success(f"✅ Staff {name} added successfully!")

# Filter
cat_filter = st.selectbox("Filter by Category", ["All", "Doctor", "Nurse", "Faculty", "PG", "Internee"])
filtered_staff = staff if cat_filter == "All" else staff[staff["Category"] == cat_filter]

st.dataframe(filtered_staff, use_container_width=True)

# ===============================
# Manage Camps
# ===============================
st.subheader("🏥 Manage Camps")

col1, col2 = st.columns(2)
with col1:
    camp_title = st.text_input("Camp Title")
with col2:
    camp_date = st.date_input("Camp Date")

if st.button("➕ Add Camp"):
    new_camp = {"Title": camp_title, "Camp Date": camp_date.strftime("%Y-%m-%d")}
    st.session_state.camps = pd.concat([st.session_state.camps, pd.DataFrame([new_camp])], ignore_index=True)
    st.success(f"✅ Camp '{camp_title}' added successfully!")

st.dataframe(st.session_state.camps, use_container_width=True)

# Assign Staff to Camps
st.subheader("🎯 Assign Staff to Camp")
if not st.session_state.camps.empty and not staff.empty:
    camp_sel = st.selectbox("Select Camp", st.session_state.camps["Title"])
    staff_sel = st.multiselect("Select Staff", staff["Name"].tolist())

    if st.button("Assign to Camp"):
        new_assignments = [{"Camp": camp_sel, "Staff": s} for s in staff_sel]
        st.session_state.camp_assignments = pd.concat(
            [st.session_state.camp_assignments, pd.DataFrame(new_assignments)], ignore_index=True
        )
        st.success("✅ Staff assigned successfully!")

st.dataframe(st.session_state.camp_assignments, use_container_width=True)

# ===============================
# Export Data
# ===============================
st.subheader("📂 Export Data")

if st.button("📤 Export All Data to Excel"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state.staff.to_excel(writer, index=False, sheet_name="Staff")
        st.session_state.camps.to_excel(writer, index=False, sheet_name="Camps")
        st.session_state.camp_assignments.to_excel(writer, index=False, sheet_name="Assignments")

    st.download_button(
        label="⬇️ Download staff_data_export.xlsx",
        data=output.getvalue(),
        file_name="staff_data_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
