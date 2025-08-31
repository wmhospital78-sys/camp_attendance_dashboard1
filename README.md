
# Camp Attendance Advanced Dashboard (with PDF export)

Features:
- SQLite-backed local app (camp.db)
- Import staff & camp data from Excel
- Category-wise dashboards (Doctors, Nursing staff, Teaching faculty, PGs with Year, Internees)
- Assign staff to camps and mark attendance
- Export reports to Excel and PDF (PDF includes overview graphs, camp schedule, and attendance summary)
- Branding header with college name and welcome message for Dr. Shabin

Run:
1. Create virtualenv and install requirements:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
2. Run:
   streamlit run app.py
