import streamlit as st
import plotly.express as px
import sqlite3
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="College Staff Dashboard",
    page_icon="🏥",
    layout="wide"
)

# ===================== DARK THEME CSS =====================
st.markdown("""
    <style>
        /* Background */
        .stApp {
            background-color: #131321;
            color: #ffffff;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1c1c2e;
            padding: 20px;
            border-radius: 20px;
            box-shadow: -2px 0px 10px rgba(0,0,0,0.8);
        }

        /* Cards */
        .card {
            background: #1e1e2f;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
            text-align: center;
        }

        .card h2 {
            color: #9b6bff;
            font-size: 28px;
        }

        .card p {
            color: #bbbbbb;
            font-size: 18px;
        }

        /* Welcome Message */
        .welcome {
            font-size: 26px;
            font-weight: bold;
            color: #ffffff;
        }

        .college {
            font-size: 20px;
            color: #9b6bff;
        }
    </style>
""", unsafe_allow_html=True)

# ===================== HEADER =====================
st.markdown('<p class="college">White Memorial Homoeopathic Medical College & Hospital</p>', unsafe_allow_html=True)
st.markdown('<p class="welcome">👋 Welcome, Dr. Shabin S</p>', unsafe_allow_html=True)

st.write("---")

# ===================== DATABASE =====================
conn = sqlite3.connect("staff_data.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_no INTEGER,
    name TEXT,
    category TEXT,
    pg_year TEXT,
    joining_date TEXT,
    camps_attended INTEGER
)
""")
conn.commit()

# ===================== DASHBOARD OVERVIEW =====================
st.subheader("📊 Dashboard Overview")

c.execute("SELECT COUNT(*) FROM staff")
total_staff = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM staff WHERE category='Doctor'")
doctors = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM staff WHERE category='Nurse'")
nurses = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM staff WHERE category='Faculty'")
faculty = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM staff WHERE category='PG'")
pgs = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM staff WHERE category='Internee'")
internees = c.fetchone()[0]

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.markdown(f"<div class='card'><h2>{total_staff}</h2><p>Total Staff</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='card'><h2>{doctors}</h2><p>Doctors</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='card'><h2>{nurses}</h2><p>Nursing Staff</p></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='card'><h2>{faculty}</h2><p>Faculty</p></div>", unsafe_allow_html=True)
with col5:
    st.markdown(f"<div class='card'><h2>{pgs}</h2><p>PGs</p></div>", unsafe_allow_html=True)
with col6:
    st.markdown(f"<div class='card'><h2>{internees}</h2><p>Internees</p></div>", unsafe_allow_html=True)

# ===================== CHARTS =====================
df = pd.read_sql("SELECT category FROM staff", conn)
if not df.empty:
    pie = px.pie(df, names="category", title="Staff Distribution")
    st.plotly_chart(pie, use_container_width=True)

# ===================== MANAGE STAFF =====================
st.subheader("👩‍⚕️ Manage Staff")

with st.expander("➕ Add New Staff"):
    with st.form("staff_form"):
        serial_no = st.number_input("Serial Number", min_value=1)
        name = st.text_input("Name")
        category = st.selectbox("Category", ["Doctor", "Nurse", "Faculty", "PG", "Internee"])
        pg_year = st.selectbox("PG Year", ["-", "1st Year", "2nd Year", "3rd Year"]) if category == "PG" else "-"
        joining_date = st.date_input("Joining Date")
        camps_attended = st.number_input("Camps Attended", min_value=0)

        submitted = st.form_submit_button("Save")
        if submitted:
            c.execute("INSERT INTO staff (serial_no, name, category, pg_year, joining_date, camps_attended) VALUES (?,?,?,?,?,?)",
                      (serial_no, name, category, pg_year, str(joining_date), camps_attended))
            conn.commit()
            st.success("✅ Staff added successfully!")

st.write("### 📋 Staff Records")
df_staff = pd.read_sql("SELECT * FROM staff", conn)
if not df_staff.empty:
    gb = GridOptionsBuilder.from_dataframe(df_staff)
    gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_default_column(editable=True)
    gridOptions = gb.build()

    grid_table = AgGrid(df_staff, gridOptions=gridOptions,
                        update_mode=GridUpdateMode.MODEL_CHANGED,
                        height=300)

    # Update database when edited
    updated = grid_table["data"]
    if not updated.empty:
        for i, row in updated.iterrows():
            c.execute("""
                UPDATE staff SET serial_no=?, name=?, category=?, pg_year=?, joining_date=?, camps_attended=? WHERE id=?
            """, (row["serial_no"], row["name"], row["category"], row["pg_year"], row["joining_date"], row["camps_attended"], row["id"]))
        conn.commit()

else:
    st.info("No staff data available. Please add staff.")

