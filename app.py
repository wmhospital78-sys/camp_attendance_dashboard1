import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Hospital Staff Dashboard", layout="wide")

# Sidebar Navigation
menu = st.sidebar.radio(
    "📌 Navigation",
    ["Dashboard Overview", "Manage Staff", "Manage Camps", "Export Data"]
)

# ================== DASHBOARD OVERVIEW ==================
if menu == "Dashboard Overview":
    st.title("🏥 Hospital Staff Dashboard Overview")

    # Example stats (replace with your real data)
    total_staff = 80
    doctors = 15
    nurses = 20
    faculty = 10
    pgs = 25
    internees = 10

    col1, col2, col3 = st.columns(3)
    col1.metric("👩‍⚕️ Total Staff", total_staff)
    col2.metric("🩺 Doctors", doctors)
    col3.metric("👩‍⚕️ Nurses", nurses)

    col4, col5 = st.columns(2)
    col4.metric("🎓 Teaching Faculty", faculty)
    col5.metric("📚 Internees", internees)

    # Pie Chart – Staff Distribution
    df = pd.DataFrame({
        "Category": ["Doctors", "Nurses", "Faculty", "PGs", "Internees"],
        "Count": [doctors, nurses, faculty, pgs, internees]
    })
    fig = px.pie(df, values="Count", names="Category", title="Staff Distribution")
    st.plotly_chart(fig, use_container_width=True)

    # Bar Chart – PGs by Year
    pg_years = pd.DataFrame({
        "Year": ["PG1", "PG2", "PG3"],
        "Count": [10, 8, 7]
    })
    fig2 = px.bar(pg_years, x="Year", y="Count", text="Count", title="PGs by Year")
    st.plotly_chart(fig2, use_container_width=True)

# ================== MANAGE STAFF ==================
elif menu == "Manage Staff":
    st.title("👩‍⚕️ Manage Staff Records")
    st.info("Here you can add, edit, delete and filter staff.")

    # Table preview (sample)
    staff_data = pd.DataFrame({
        "S.No": [1,2,3],
        "Name": ["Dr. A", "Nurse B", "PG C"],
        "Category": ["Doctor", "Nurse", "PG"],
        "PG Year": ["-", "-", "PG1"],
        "Joining Date": ["2022-01-01", "2023-05-12", "2024-07-10"],
        "Camps Attended": [5, 2, 3]
    })
    st.dataframe(staff_data, use_container_width=True)

# ================== MANAGE CAMPS ==================
elif menu == "Manage Camps":
    st.title("🏥 Manage Camps")
    st.info("Add new camps, assign staff, and view camp-wise staff list.")

# ================== EXPORT DATA ==================
elif menu == "Export Data":
    st.title("📂 Export Data to Excel")
    st.info("Download staff, camps, and assignments as one Excel file.")

    staff_data = pd.DataFrame({
        "S.No": [1,2,3],
        "Name": ["Dr. A", "Nurse B", "PG C"],
        "Category": ["Doctor", "Nurse", "PG"],
        "Joining Date": ["2022-01-01", "2023-05-12", "2024-07-10"],
        "Camps Attended": [5, 2, 3]
    })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        staff_data.to_excel(writer, index=False, sheet_name="Staff")

    st.download_button(
        label="📥 Download staff_data_export.xlsx",
        data=output.getvalue(),
        file_name="staff_data_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
