import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Camp Attendance Dashboard", layout="wide")

# ---------------------------
# Welcome Header
# ---------------------------
st.markdown("<h2 style='text-align:center; color:teal;'>White Memorial Homoeo Medical College & Hospital</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'>Attoor, Veeyanoor (PO), Kanniyakumari District</h4>", unsafe_allow_html=True)
st.markdown("---")
st.success("👋 Welcome Dr. Shabin — Hospital Admin")

# ---------------------------
# Initialize session state
# ---------------------------
if "staff" not in st.session_state:
    st.session_state.staff = pd.DataFrame(columns=["Name", "Category", "Year"])
if "camps" not in st.session_state:
    st.session_state.camps = pd.DataFrame(columns=["title", "camp_date"])
if "camp_assignments" not in st.session_state:
    st.session_state.camp_assignments = pd.DataFrame(columns=["Camp", "Staff"])

# ---------------------------
# Sidebar Navigation
# ---------------------------
menu = st.sidebar.radio("📌 Navigation", ["Overview", "Manage Staff", "Manage Camps", "Export Data"])

# ---------------------------
# Overview
# ---------------------------
if menu == "Overview":
    st.header("📊 Staff Overview")

    df = st.session_state.staff

    if df.empty:
        st.info("No staff data available. Please add staff in 'Manage Staff'.")
    else:
        # Category distribution pie chart
        cat_counts = df["Category"].value_counts()

        fig, ax = plt.subplots()
        ax.pie(cat_counts, labels=cat_counts.index, autopct="%1.1f%%", startangle=90)
        ax.set_title("Staff Distribution by Category")
        st.pyplot(fig)

        st.subheader("📋 Staff Count by Category")
        st.write(cat_counts)

        # Filter option
        cat_filter = st.multiselect("Filter by Category", df["Category"].unique(), default=df["Category"].unique())
        st.dataframe(df[df["Category"].isin(cat_filter)])

# ---------------------------
# Manage Staff
# ---------------------------
elif menu == "Manage Staff":
    st.header("👩‍⚕️ Manage Staff Data")

    with st.form("add_staff_form"):
        name = st.text_input("Staff Name")
        category = st.selectbox("Category", ["Doctor", "Nursing Staff", "Teaching Faculty", "PG", "Internee"])
        year = None
        if category == "PG":
            year = st.number_input("Enter PG Year", min_value=1, max_value=5, step=1)
        submitted = st.form_submit_button("Add Staff")

        if submitted and name:
            st.session_state.staff = pd.concat(
                [st.session_state.staff, pd.DataFrame([[name, category, year]], columns=["Name", "Category", "Year"])],
                ignore_index=True
            )
            st.success(f"✅ {name} added as {category}")

    st.subheader("📋 Current Staff")
    st.dataframe(st.session_state.staff)

# ---------------------------
# Manage Camps
# ---------------------------
elif menu == "Manage Camps":
    st.header("🏥 Camp Management")

    with st.form("add_camp_form"):
        title = st.text_input("Camp Title")
        camp_date = st.date_input("Camp Date")
        add_camp = st.form_submit_button("Add Camp")

        if add_camp and title:
            st.session_state.camps = pd.concat(
                [st.session_state.camps, pd.DataFrame([[title, camp_date]], columns=["title", "camp_date"])],
                ignore_index=True
            )
            st.success(f"✅ Camp '{title}' added.")

    st.subheader("📋 Existing Camps")
    st.dataframe(st.session_state.camps)

    if not st.session_state.camps.empty and not st.session_state.staff.empty:
        st.subheader("👥 Assign Staff to Camps")

        camp_sel = st.selectbox("Select Camp", [f"{r['title']} — {r['camp_date']}" for _, r in st.session_state.camps.iterrows()])
        staff_sel = st.multiselect("Select Staff", st.session_state.staff["Name"].tolist())

        if st.button("Assign"):
            for s in staff_sel:
                st.session_state.camp_assignments = pd.concat(
                    [st.session_state.camp_assignments, pd.DataFrame([[camp_sel, s]], columns=["Camp", "Staff"])],
                    ignore_index=True
                )
            st.success("✅ Staff assigned to camp successfully.")

        st.subheader("📋 Camp Assignments")
        st.dataframe(st.session_state.camp_assignments)

# ---------------------------
# Export Data
# ---------------------------
elif menu == "Export Data":
    st.header("📂 Export Data")

    df = st.session_state.staff
    camps = st.session_state.camps
    assign = st.session_state.camp_assignments

    if st.button("Export All Data to Excel"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            if not df.empty:
                df.to_excel(writer, index=False, sheet_name="Staff")
            if not camps.empty:
                camps.to_excel(writer, index=False, sheet_name="Camps")
            if not assign.empty:
                assign.to_excel(writer, index=False, sheet_name="Assignments")

        st.download_button(
            label="📥 Download Excel",
            data=output.getvalue(),
            file_name="staff_data_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("✅ Data Exported Successfully")
