import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# App Title
st.set_page_config(page_title="Camp Attendance Dashboard", layout="wide")

st.markdown("<h2 style='text-align: center; color: teal;'>White Memorial Homoeo Medical College & Hospital</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Attoor, Veeyanoor P.O, Kanniyakumari District</h4>", unsafe_allow_html=True)
st.markdown("---", unsafe_allow_html=True)

# Welcome message
st.sidebar.success("Welcome Dr. Shabin — Hospital Admin")

DATA_FILE = "staff_data.xlsx"
CAMP_FILE = "camp_schedule.xlsx"

# Load or initialize staff data
if os.path.exists(DATA_FILE):
    staff_df = pd.read_excel(DATA_FILE)
else:
    staff_df = pd.DataFrame(columns=["Sl No", "Name", "Category", "Joining Date", "Year", "Camps Attended"])

# Save function
def save_data(df, filename):
    df.to_excel(filename, index=False)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Master Data", "📊 Overview", "📅 Camp Schedule", "📝 Reports", "⬆️ Import/Export"])

# Master Data
with tab1:
    st.subheader("Master Data Entry")
    col1, col2, col3 = st.columns(3)
    with col1:
        sl_no = st.number_input("Sl No", min_value=1)
    with col2:
        name = st.text_input("Name")
    with col3:
        category = st.selectbox("Category", ["Doctor", "Nursing Staff", "Teaching Faculty", "PG", "Internee"])

    year = None
    if category == "PG":
        year = st.selectbox("PG Year", ["1st Year", "2nd Year", "3rd Year"])

    joining_date = st.date_input("Joining Date", datetime.today())
    camps_attended = st.number_input("Camps Attended", min_value=0)

    if st.button("➕ Add Staff"):
        new_entry = {"Sl No": sl_no, "Name": name, "Category": category, "Joining Date": joining_date, "Year": year, "Camps Attended": camps_attended}
        staff_df = pd.concat([staff_df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(staff_df, DATA_FILE)
        st.success("✅ Staff Added Successfully!")

    st.dataframe(staff_df)

# Overview Tab
with tab2:
    st.subheader("Overview Dashboard")

    if not staff_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Attendance by Category")
            category_counts = staff_df.groupby("Category")["Camps Attended"].sum()
            fig1, ax1 = plt.subplots()
            category_counts.plot(kind="bar", ax=ax1)
            st.pyplot(fig1)

        with col2:
            st.markdown("### Attendance Distribution")
            fig2, ax2 = plt.subplots()
            staff_df["Camps Attended"].plot(kind="hist", bins=10, ax=ax2)
            st.pyplot(fig2)

        st.markdown("### Category-wise Pie Chart")
        fig3, ax3 = plt.subplots()
        staff_df["Category"].value_counts().plot.pie(autopct="%1.1f%%", ax=ax3)
        st.pyplot(fig3)

# Camp Schedule
with tab3:
    st.subheader("Camp Scheduling")
    if os.path.exists(CAMP_FILE):
        camps = pd.read_excel(CAMP_FILE)
    else:
        camps = pd.DataFrame(columns=["Title", "Camp Date", "Staff Assigned"])

    camp_title = st.text_input("Camp Title")
    camp_date = st.date_input("Camp Date")
    staff_selected = st.multiselect("Assign Staff", staff_df["Name"].tolist())

    if st.button("➕ Add Camp"):
        new_camp = {"Title": camp_title, "Camp Date": camp_date, "Staff Assigned": ", ".join(staff_selected)}
        camps = pd.concat([camps, pd.DataFrame([new_camp])], ignore_index=True)
        save_data(camps, CAMP_FILE)
        st.success("✅ Camp Scheduled Successfully!")

    st.dataframe(camps)

# Reports Tab
with tab4:
    st.subheader("Reports & Analysis")
    if not staff_df.empty:
        category_filter = st.selectbox("Select Category", ["All"] + staff_df["Category"].unique().tolist())
        if category_filter != "All":
            filtered_df = staff_df[staff_df["Category"] == category_filter]
        else:
            filtered_df = staff_df
        st.dataframe(filtered_df)

        if st.button("📤 Export Report to Excel"):
            report_file = "attendance_report.xlsx"
            filtered_df.to_excel(report_file, index=False)
            st.success(f"Report exported successfully as {report_file}")

# Import / Export
with tab5:
    st.subheader("Import / Export Excel")
    uploaded = st.file_uploader("Upload Staff Excel File", type=["xlsx"])
    if uploaded:
        staff_df = pd.read_excel(uploaded)
        save_data(staff_df, DATA_FILE)
        st.success("✅ Data Imported Successfully!")
        st.dataframe(staff_df)

    if st.button("⬇️ Download Current Data"):
        staff_df.to_excel("staff_data_export.xlsx", index=False)
        st.success("✅ Data Exported Successfully as staff_data_export.xlsx")
