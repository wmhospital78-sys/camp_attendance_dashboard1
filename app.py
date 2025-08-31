import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="Hospital Staff Dashboard", layout="wide")

# ===================== COLOR THEME =====================
PRIMARY = "#061F40"   # Sidebar / header
DARK = "#051326"      # Cards
GRAY = "#979DA6"      # Subtext
ACCENT = "#062540"    # Borders / highlights
LIGHT = "#F2F2F2"     # Background

# ===================== CSS =====================
st.markdown(f"""
    <style>
    .main {{
        background-color: {LIGHT};
    }}
    .sidebar .sidebar-content {{
        background-color: {PRIMARY};
        color: white;
    }}
    .stButton>button {{
        background-color: {PRIMARY};
        color: white;
        border-radius: 8px;
        padding: 8px 20px;
    }}
    .stButton>button:hover {{
        background-color: {ACCENT};
    }}
    .metric-card {{
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
    }}
    .metric-value {{
        font-size: 28px;
        font-weight: bold;
        color: {PRIMARY};
    }}
    .metric-label {{
        color: {GRAY};
        font-size: 14px;
    }}
    </style>
""", unsafe_allow_html=True)

# ===================== DATA =====================
if "staff" not in st.session_state:
    st.session_state.staff = pd.DataFrame(columns=[
        "Serial No", "Name", "Category", "PG Year", "Joining Date", "Camps Attended"
    ])

if "camps" not in st.session_state:
    st.session_state.camps = pd.DataFrame(columns=["Camp Title", "Date", "Assigned Staff"])

# ===================== SIDEBAR =====================
st.sidebar.title("🏥 Hospital Dashboard")
menu = st.sidebar.radio("Navigation", ["Overview", "Manage Staff", "Manage Camps", "Export Data"])

# ===================== OVERVIEW =====================
if menu == "Overview":
    st.title("📊 Dashboard Overview")

    staff = st.session_state.staff

    total_staff = len(staff)
    doctors = len(staff[staff["Category"] == "Doctor"])
    nurses = len(staff[staff["Category"] == "Nurse"])
    faculty = len(staff[staff["Category"] == "Faculty"])
    pgs = len(staff[staff["Category"] == "PG"])
    internees = len(staff[staff["Category"] == "Internee"])

    # Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_staff}</div><div class='metric-label'>Total Staff</div></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='metric-card'><div class='metric-value'>{doctors}</div><div class='metric-label'>Doctors</div></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='metric-card'><div class='metric-value'>{nurses}</div><div class='metric-label'>Nursing Staff</div></div>", unsafe_allow_html=True)
    with col4: st.markdown(f"<div class='metric-card'><div class='metric-value'>{faculty}</div><div class='metric-label'>Faculty</div></div>", unsafe_allow_html=True)
    with col5: st.markdown(f"<div class='metric-card'><div class='metric-value'>{pgs}</div><div class='metric-label'>PGs</div></div>", unsafe_allow_html=True)

    # Charts
    if not staff.empty:
        st.subheader("📈 Staff Distribution by Category")
        pie = px.pie(staff, names="Category", title="Staff Distribution")
        st.plotly_chart(pie, use_container_width=True)

        st.subheader("📊 PGs by Year")
        pg_data = staff[staff["Category"] == "PG"].groupby("PG Year").size().reset_index(name="Count")
        if not pg_data.empty:
            bar = px.bar(pg_data, x="PG Year", y="Count", title="PGs by Year", text="Count")
            st.plotly_chart(bar, use_container_width=True)

# ===================== MANAGE STAFF =====================
elif menu == "Manage Staff":
    st.title("👩‍⚕️ Manage Staff")

    with st.form("add_staff"):
        serial = st.text_input("Serial No")
        name = st.text_input("Name")
        category = st.selectbox("Category", ["Doctor", "Nurse", "Faculty", "PG", "Internee"])
        pg_year = st.selectbox("PG Year", ["-", "1st Year", "2nd Year", "3rd Year"]) if category == "PG" else "-"
        joining = st.date_input("Joining Date")
        camps_attended = st.number_input("Camps Attended", min_value=0, step=1)
        submitted = st.form_submit_button("Add Staff")

        if submitted:
            st.session_state.staff = pd.concat([
                st.session_state.staff,
                pd.DataFrame([[serial, name, category, pg_year, str(joining), camps_attended]],
                             columns=st.session_state.staff.columns)
            ], ignore_index=True)
            st.success(f"Added staff: {name}")

    st.subheader("📋 Staff Table")
    st.dataframe(st.session_state.staff, use_container_width=True)

# ===================== MANAGE CAMPS =====================
elif menu == "Manage Camps":
    st.title("🏥 Manage Camps")

    with st.form("add_camp"):
        title = st.text_input("Camp Title")
        date = st.date_input("Camp Date")
        staff_options = st.multiselect("Assign Staff", st.session_state.staff["Name"].tolist())
        submitted = st.form_submit_button("Add Camp")

        if submitted:
            st.session_state.camps = pd.concat([
                st.session_state.camps,
                pd.DataFrame([[title, str(date), ", ".join(staff_options)]],
                             columns=st.session_state.camps.columns)
            ], ignore_index=True)
            st.success(f"Camp added: {title}")

    st.subheader("📋 Camps Table")
    st.dataframe(st.session_state.camps, use_container_width=True)

# ===================== EXPORT DATA =====================
elif menu == "Export Data":
    st.title("📂 Export Data")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state.staff.to_excel(writer, index=False, sheet_name="Staff")
        st.session_state.camps.to_excel(writer, index=False, sheet_name="Camps")
    excel_data = output.getvalue()

    st.download_button(
        label="⬇ Download Excel File",
        data=excel_data,
        file_name="staff_data_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
