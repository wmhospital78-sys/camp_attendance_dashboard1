import streamlit as st
import pandas as pd
import sqlite3
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ================== DATABASE SETUP ==================
conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                department TEXT,
                designation TEXT,
                joining_date TEXT,
                phone TEXT,
                email TEXT
            )''')
conn.commit()

# ================== SIDEBAR STYLING ==================
def sidebar_ui():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background-color: #131321;
            padding: 1rem;
            box-shadow: 4px 0px 10px rgba(0,0,0,0.7);
        }
        [data-testid="stSidebar"] .css-1v0mbdj, 
        [data-testid="stSidebar"] .css-17lntkn {
            display: none;
        }
        .sidebar-title {
            font-size: 20px;
            font-weight: bold;
            color: white;
            text-align: center;
            margin-bottom: 10px;
        }
        .sidebar-user {
            font-size: 14px;
            color: #9f9fb1;
            text-align: center;
            margin-bottom: 20px;
        }
        .sidebar-item {
            padding: 12px 20px;
            border-radius: 10px;
            margin: 8px 0px;
            color: #cfcfe1;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .sidebar-item:hover {
            background: linear-gradient(90deg, #6a11cb, #2575fc);
            color: white;
            transform: translateX(4px);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.markdown('<div class="sidebar-title">🏥 White Memorial Homoeopathic <br> Medical College & Hospital</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-user">👋 Welcome, Dr. Shabin S <br><small>Hospital Admin</small></div>', unsafe_allow_html=True)

        menu = st.radio(
            "Navigation", 
            ["Dashboard", "Add Staff", "Manage Staff", "Reports", "Settings"], 
            label_visibility="collapsed"
        )
    return menu

# ================== PAGES ==================
def dashboard():
    st.title("📊 Hospital Overview")
    staff_count = c.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
    st.metric("👨‍⚕️ Total Staff", staff_count)

def add_staff():
    st.title("➕ Add Staff")
    with st.form("add_staff_form"):
        name = st.text_input("Name")
        dept = st.text_input("Department")
        desig = st.text_input("Designation")
        join = st.date_input("Joining Date")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Add")
        if submitted:
            c.execute("INSERT INTO staff (name, department, designation, joining_date, phone, email) VALUES (?,?,?,?,?,?)",
                      (name, dept, desig, str(join), phone, email))
            conn.commit()
            st.success("✅ Staff added successfully!")

    st.markdown("---")
    st.subheader("📂 Upload Staff Excel")
    file = st.file_uploader("Upload Excel", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        df.to_sql("staff", conn, if_exists="append", index=False)
        st.success("✅ Excel data uploaded successfully!")

def manage_staff():
    st.title("📝 Manage Staff Records")
    df = pd.read_sql("SELECT * FROM staff", conn)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(editable=True)
    gb.configure_selection('single', use_checkbox=True)
    gridoptions = gb.build()

    grid = AgGrid(df, gridOptions=gridoptions, update_mode=GridUpdateMode.MODEL_CHANGED, height=400)

    if grid["data"] is not None:
        updated_df = grid["data"]
        if st.button("💾 Save Changes"):
            for index, row in updated_df.iterrows():
                c.execute("UPDATE staff SET name=?, department=?, designation=?, joining_date=?, phone=?, email=? WHERE id=?",
                          (row["name"], row["department"], row["designation"], row["joining_date"], row["phone"], row["email"], row["id"]))
            conn.commit()
            st.success("✅ Records updated!")

    if st.button("🗑️ Delete Selected"):
        sel = grid["selected_rows"]
        if sel:
            staff_id = sel[0]["id"]
            c.execute("DELETE FROM staff WHERE id=?", (staff_id,))
            conn.commit()
            st.warning(f"🚨 Staff ID {staff_id} deleted!")

def reports():
    st.title("📑 Reports")
    df = pd.read_sql("SELECT department, COUNT(*) as staff_count FROM staff GROUP BY department", conn)
    st.bar_chart(df.set_index("department"))
    st.table(df)

def settings():
    st.title("⚙️ Settings")
    theme = st.radio("Choose Theme", ["Dark", "Light"])
    if theme == "Light":
        st.markdown(
            """<style>[data-testid="stSidebar"] {background:#f9f9f9; color:black;}</style>""",
            unsafe_allow_html=True
        )
        st.success("🌞 Light theme applied!")
    else:
        st.markdown(
            """<style>[data-testid="stSidebar"] {background:#131321; color:white;}</style>""",
            unsafe_allow_html=True
        )
        st.success("🌙 Dark theme applied!")

# ================== MAIN ==================
def main():
    menu = sidebar_ui()

    if menu == "Dashboard":
        dashboard()
    elif menu == "Add Staff":
        add_staff()
    elif menu == "Manage Staff":
        manage_staff()
    elif menu == "Reports":
        reports()
    elif menu == "Settings":
        settings()

if __name__ == "__main__":
    main()
