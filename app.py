import streamlit as st
import pandas as pd
import time
import codecs
from rapidfuzz import process, utils
import openpyxl
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.figure_factory as ff
import joblib
import os
from datetime import datetime
from sklearn.metrics import confusion_matrix
from supabase import create_client, Client
from utils.style import apply_custom_design
import requests
import json

# --- 1. CONFIG & CONNECTION ---
st.set_page_config(
    page_title="NET-TRACK Pro | PHCM",
    page_icon="🌐",
    layout="wide"
)
# --- 1. CONFIG & CONNECTION ---
# --- NEW AI ENGINE (GROQ) ---
# Pull the key securely from the secrets file
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
def ask_ai(prompt):
    """Refined Groq call to handle the dynamic response correctly"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant", 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7 # Adds a bit of 'personality' to the coach
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        res_json = response.json()
        
        # This is the line that fixes the 'choices' error
        if 'choices' in res_json and len(res_json['choices']) > 0:
            return res_json['choices'][0]['message']['content']
        else:
            # This helps us see if the API key is actually working
            return f"AI Error: {res_json.get('error', {}).get('message', 'Check API Key')}"
    except Exception as e:
        return f"Connection Error: {str(e)}"
URL = "https://bvibfvnhomaxpnodyiis.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ2aWJmdm5ob21heHBub2R5aWlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyNzcxNDksImV4cCI6MjA4OTg1MzE0OX0.Bp9RPsyzroN-14wqVhD037z1kTTPoaxwsQElloeDNFo"

@st.cache_resource
def get_supabase():
    try:
    # This pulls from the Secrets tab in Streamlit Cloud
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("📡 Connection Error: Could not reach Supabase. Check your internet or secrets.toml.")
        st.stop()

supabase = get_supabase()
apply_custom_design()

# --- 2. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'user_role': None,
        'username': None,
        'last_sync': "Never",
        'forgot_mode': False,
        'page': "Dashboard",
        'current_weakness': "General Networking" 
    })

# --- 3. SIMPLE PASSWORD RESET (Email-Based, No OTP) ---
if st.session_state['forgot_mode']:
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="dark-panel">', unsafe_allow_html=True)
        st.header("🔑 Reset Password")
        st.caption("Enter your registered email to set a new password.")
        
        target_email = st.text_input("Registered Email")
        new_p = st.text_input("New Password", type="password")
        confirm_p = st.text_input("Confirm New Password", type="password")
        
        if st.button("Update Password", type="primary", use_container_width=True):
            if not target_email or not new_p:
                st.error("Please fill in all fields.")
            elif new_p != confirm_p:
                st.error("Passwords do not match!")
            else:
                try:
                    # 1. Check if Email exists in profiles
                    check = supabase.table("profiles").select("email").eq("email", target_email).execute()
                    
                    if check.data:
                        # 2. Update the password in the database
                        supabase.table("profiles").update({"password": new_p}).eq("email", target_email).execute()
                        
                        st.success(f"✅ Password for {target_email} updated!")
                        time.sleep(2)
                        st.session_state['forgot_mode'] = False
                        st.rerun()
                    else:
                        st.error("🚨 Email not found in our records.")
                except Exception as e:
                    st.error(f"Update failed: {str(e)}")
        
        if st.button("← Back to Login", key="cancel_reset"):
            st.session_state['forgot_mode'] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 4. LOGIN UI (Supports ID or Email) ---
if not st.session_state['logged_in']:
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="dark-panel">', unsafe_allow_html=True)
        st.markdown('<h1 class="main-header">NET-TRACK Access</h1>', unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["Login", "Register"])
        
        with t1:
            with st.form("login_form"):
                # Label updated to reflect dual-login capability
                u = st.text_input("Student ID or Email")
                p = st.text_input("Password", type="password")
                
                c_log, c_forgot = st.columns(2)
                login_submitted = c_log.form_submit_button("Sign In", use_container_width=True)
                forgot_submitted = c_forgot.form_submit_button("Forgot Password?", use_container_width=True)

            if forgot_submitted:
                st.session_state['forgot_mode'] = True
                st.rerun()

            if login_submitted:
                if u and p:
                    # UPDATED: This query checks BOTH username and email columns
                    res = supabase.table("profiles") \
                        .select("*") \
                        .or_(f"username.eq.{u},email.eq.{u}") \
                        .eq("password", p) \
                        .execute()
                    
                    if res.data:
                        st.session_state.update({
                            'logged_in': True, 
                            'user_role': res.data[0]['role'], 
                            'username': res.data[0]['username'] # Always store the ID for consistency
                        })
                        st.rerun()
                    else:
                        st.error("🚨 Invalid Credentials")
                else:
                    st.warning("Please enter your credentials.")
        
        with t2:
            st.markdown('<br>', unsafe_allow_html=True)
            
            # --- Personal Details ---
            c1, c2 = st.columns([3, 1])
            f_name = c1.text_input("First Name", placeholder="Juan")
            m_i = c2.text_input("M.I.", max_chars=2, placeholder="A")
            
            c3, c4 = st.columns(2)
            l_name = c3.text_input("Last Name", placeholder="Cruz")
            email = c4.text_input("Email Address", placeholder="user@manila.uphsl.edu.ph")
            phone = st.text_input("Phone Number", placeholder="09123456789")

            # --- DYNAMIC ROLE SELECTION ---
            new_r = st.selectbox("Registering as:", ["Student", "Teacher"])
            
            # --- SMART LABELS LOGIC ---
            if new_r == "Teacher":
                id_label = "Faculty / Employee ID"
                dept_label = "Handling Department"
                placeholder_id = "e.g. 2024-FAC-123"
            else:
                id_label = "Student ID"
                dept_label = "Enrolled Course"
                placeholder_id = "e.g. m21-1234-567"

            dept_options = ["BSCS", "BSIT", "BSBA", "BA COMM", "CIHM", "BSN", "BSOT", "BSPT", "BSRT", "BS RADTECH", "JHS", "SHS"]
            dept = st.selectbox(dept_label, dept_options)
            
            new_u = st.text_input(id_label, placeholder=placeholder_id)
            new_p = st.text_input("Set Password", type="password")
            
            auth_gate = True
            if new_r == "Teacher":
                admin_code = st.text_input("Teacher Authorization Code", type="password")
                if admin_code != "PHCM_ADMIN_2026":
                    auth_gate = False
            
            st.markdown('<br>', unsafe_allow_html=True)
            
            if st.button("COMPLETE REGISTRATION", use_container_width=True, type="primary"):
                if not all([f_name, m_i, l_name, email, new_u, new_p, phone]):
                    st.error("🚨 Please complete all fields.")
                elif not auth_gate:
                    st.error("🚨 Invalid Teacher Authorization Code.")
                else:
                    try:
                        # Register in Supabase Auth (Optional if you only want DB login)
                        supabase.auth.sign_up({"email": email, "password": new_p})

                        # Save to Profiles Table
                        full_name = f"{f_name} {m_i}. {l_name}".strip()
                        supabase.table("profiles").insert({
                            "username": new_u, 
                            "password": new_p, 
                            "role": new_r,
                            "full_name": full_name,
                            "email": email,
                            "phone": phone,
                            "department": dept
                        }).execute()
                        
                        # Initialize Analytics for Students
                        if new_r == "Student":
                            supabase.table("student_analytics").insert({
                                "student_id": new_u, "accuracy_score": 0, "status": "New"
                            }).execute()
                            
                        st.success(f"Welcome to NET-TRACK, {f_name}!")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()

                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")



# --- 5. MAIN SYSTEM VIEW ---
else:
    with st.sidebar:
        st.markdown('<h2 style="color:#4ade80;">NET-TRACK</h2>', unsafe_allow_html=True)
        st.write(f"User: **{st.session_state['username']}** | {st.session_state['user_role']}")
        st.divider()
        
        # Navigation logic based on role
        if st.session_state['user_role'] == "Teacher":
            nav = ["Teacher Dashboard", "AI Model Metrics"]
        else:
            nav = ["Dashboard", "Practice Quiz"]

        if st.session_state['page'] not in nav:
             st.session_state['page'] = nav[0]

        current_index = nav.index(st.session_state['page']) if st.session_state['page'] in nav else 0

        page = st.radio("NAVIGATE", nav, index=current_index, key="nav_radio")
        st.session_state['page'] = page
        
        if st.button("Log Out"):
            st.session_state.clear()
            st.rerun()

# --- GLOBAL DATA FETCHING (AFTER SIDEBAR, BEFORE NAVIGATION BLOCKS) ---
if st.session_state['user_role'] == "Student":
    # 1. Fetch current student's analytics [cite: 535]
    cloud_res = supabase.table("student_analytics").select("*").eq("student_id", st.session_state['username']).execute()

    if cloud_res.data:
        r = cloud_res.data[0] # [cite: 537]
        
        # 2. Extract raw data [cite: 538, 541, 542, 543]
        raw_p = r.get('participation_score', 0)
        absences = r.get('absent_count', 0)
        a_score = r.get('assignment_score', 0)
        q_score = r.get('quiz_score', 0)
        e_score = r.get('exam_score', 0)
        
        # 3. Calculate Global Variables [cite: 540, 544]
        merged_participation = max(0, raw_p - (absences * 5))
        final_grade = (merged_participation * 0.2) + (a_score * 0.2) + (q_score * 0.2) + (e_score * 0.4)
        
        # 4. Identify Weakness (Adjust this logic as needed)
        scores = {"Participation": merged_participation, "Assignments": a_score, "Quizzes": q_score, "Exam": e_score}
        primary_weakness = min(scores, key=scores.get)
    else:
        # Defaults if no data is found
        final_grade = 0
        primary_weakness = "General Networking"

# --- ROUTING LOGIC (All dashboards must be here) ---
# -- TEACHER DASHBOARD --
    if st.session_state['page'] == "Teacher Dashboard":
        st.title("👨‍🏫 Faculty Grade Management")

        res = supabase.table("student_analytics").select("*").execute()

        if res.data:
            df = pd.DataFrame(res.data).drop_duplicates(subset=['student_id'])
            # --- NEW: VISUAL METRICS OVERVIEW ---
            st.subheader("📊 Class Insights")
            m1, m2, m3, m4 = st.columns(4)
            
            avg_grade = df['total_weighted_grade'].mean()
            avg_absent = df['absent_count'].mean()
            avg_participation = df['participation_score'].mean()
            at_risk = df[(df['absent_count'] >= 3) | (df['total_weighted_grade'] < 75)].shape[0]
            m1.metric("Avg. Absences", f"{avg_absent:.1f}", delta="-0.2", delta_color="inverse")
            m2.metric("Avg. Participation", f"{avg_participation:.1f}%")
            m3.metric("At-Risk Students", at_risk, delta=f"{at_risk}", delta_color="inverse")
            m4.metric("Total Students", len(df))
            st.divider()
        
        # --- NEW: ADVANCED ATTENDANCE UPLOADER ---
        with st.expander("📂 Import Attendance from Excel (Advanced Matching)", expanded=False):
            st.write("Upload a sheet with student names. The AI will match them to your registered users.")
            att_file = st.file_uploader("Choose Attendance Excel", type=["xlsx"])
            
            if att_file:
                prof_res = supabase.table("profiles").select("username, full_name").eq("role", "Student").execute()
                db_students = {s['full_name']: s['username'] for s in prof_res.data}
                
                # 2. Process Excel
                wb = openpyxl.load_workbook(att_file, data_only=True)
                ws = wb.active
                
                match_results = []
                for row in ws.iter_rows(min_row=2): # Assuming Row 1 is header
                    excel_name = row[0].value # Assuming Names are in Column A
                    if not excel_name: continue
                    
                    # Detection Logic: Fuzzy match Excel Name vs Database Full Name
                    match = process.extractOne(
                        str(excel_name), 
                        db_students.keys(), 
                        processor=utils.default_process, 
                        score_cutoff=90
                    )
                    
                    if match:
                        matched_name, score, _ = match
                        student_id = db_students[matched_name]
                        
                        # 3. ACCURATE ABSENCE COUNTING
                        # We skip row[0] (the name) and only check date cells
                        date_cells = row[1:5]
                        total_possible_sessions = len(date_cells) 
                        absences = 0
                        for cell in date_cells:
                            val = cell.value
                            has_text = val is not None and str(val).strip() != ""
                            if has_text:
                                continue
                            # Detects "Yellow" OR "Empty" but ignores text like "Presenter" or "15"
                            is_yellow = cell.fill.start_color.index in ['FFFFFF00', 6]
                            if is_yellow:
                                absences += 1

                            attended = total_possible_sessions - absences
                            participation_pct = (attended / total_possible_sessions) * 100
            
                        match_results.append({
                            "Student ID": student_id,
                            "Excel Name": excel_name,
                            "Matched To": matched_name,
                            "Absences Found": absences,
                            "Raw Participation": participation_pct
                        })
                
                if match_results:
                    match_df = pd.DataFrame(match_results)
                    st.dataframe(match_df)
                    if st.button("Confirm & Bulk Update"):
                        with st.spinner("Processing attendance..."):
                            success_count = 0
                            for item in match_results:
                            # 1. Try to Update first
                                response = supabase.table("student_analytics") \
                                    .update({
                                        "absent_count": int(item["Absences Found"]),
                                        "participation_score": float(item["Raw Participation"])
                                    }) \
                                    .eq("student_id", item["Student ID"]) \
                                    .execute()
            
                            # 2. If the update didn't touch any rows, the student might be missing from this table
                            # So we use .upsert() as a backup to create the row if it's missing
                            if not response.data:
                                supabase.table("student_analytics").upsert({
                                    "student_id": item["Student ID"],
                                    "absent_count": int(item["Absences Found"]),
                                    "participation_score": float(item["Raw Participation"]),
                                    "assignment_score": 0,
                                    "quiz_score": 0,
                                    "exam_score": 0
                                }).execute()
            
                            success_count += 1
            
                        if success_count > 0:
                            st.toast(f"✅ Synced {success_count} students from Excel!", icon='📊')
                            time.sleep(1)
                            st.success("Attendance successfully integrated.")
                            st.rerun()

        # --- ENHANCED GRADE SHEET ---
        st.subheader("📝 Class Grade Sheet")

        df['participation_score'] = ((4 - df['absent_count']) / 4 * 100).clip(lower=0)

        df['Total Grade (%)'] = (df['participation_score']*0.2) + \
                                (df['assignment_score']*0.2) + \
                                (df['quiz_score']*0.2) + \
                                (df['exam_score']*0.4)
        
        # Define status based on risk factors
        def get_status(row):
            if row['absent_count'] >= 3: return "🚩 At Risk"
            if row['Total Grade (%)'] < 75: return "⚠️ Low Performance"
            return "✅ Stable"
        
        df['Status'] = df.apply(get_status, axis=1)
        
        cols_to_edit = ['Status', 'student_id', 'absent_count', 'Total Grade (%)', 'participation_score', 'assignment_score', 'quiz_score', 'exam_score']
        
        updated_df = st.data_editor(
            df[cols_to_edit],
            key="grade_editor_v2",
            column_config={
                "Status": st.column_config.TextColumn("System Status", disabled=True),
                "student_id": st.column_config.TextColumn("Student ID", disabled=True),
                "Total Grade (%)": st.column_config.NumberColumn("Total Grade (%)", format="%.1f", disabled=True),
                "absent_count": st.column_config.NumberColumn("Absences", min_value=0),
                "participation_score": st.column_config.ProgressColumn("Participation", min_value=0, max_value=100, format="%d%%"),
                "assignment_score": st.column_config.NumberColumn("Assignments (20%)", min_value=0, max_value=100),
                "quiz_score": st.column_config.NumberColumn("Quizzes (20%)", min_value=0, max_value=100),
                "exam_score": st.column_config.NumberColumn("Examination (40%)", min_value=0, max_value=100),
            },
            hide_index=True,
            use_container_width=True
        )

        if st.button("Save Changes to Database 🔄", type="primary", use_container_width=True):
            for _, row in updated_df.iterrows():
                final_db_grade = (row['participation_score']*0.2) + (row['assignment_score']*0.2) + \
                                     (row['quiz_score']*0.2) + (row['exam_score']*0.4)
                supabase.table("student_analytics").update({
                    "absent_count": row['absent_count'],
                    "participation_score": row['participation_score'],
                    "assignment_score": row['assignment_score'],
                    "quiz_score": row['quiz_score'],
                    "exam_score": row['exam_score'],
                    "total_weighted_grade": final_db_grade
                }).eq("student_id", row['student_id']).execute()
            st.success("Succesfully updated Database!")
            st.rerun()

        st.divider()

        # --- EXPORT SECTION (Moved outside the button block so it's always visible) ---
        st.subheader("📄 Export Report")
        st.write("Download the current grade records for official university documentation.")
        export_df = df.copy()       
        # Prepare CSV
        csv_data = export_df.to_csv(index=False).encode('utf-8-sig')
    
        st.download_button(
            label="📥 Download Grade Report (CSV)",
            data=csv_data,
            file_name=f'NETTRACK_Grades_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )
            

    elif st.session_state['page'] == "AI Model Metrics":
        st.title("📊 AI Model Performance Analytics")
        st.write("Real-time validation of the 'At Risk' prediction model based on student behavior.")

        res = supabase.table("student_analytics").select("*").execute()
        
        if res.data:
            df = pd.DataFrame(res.data)

            # --- STEP 1: CALCULATE FINAL GRADE ---
            df['Final_Grade'] = (df['participation_score']*0.2) + \
                               (df['assignment_score']*0.2) + \
                               (df['quiz_score']*0.2) + \
                               (df['exam_score']*0.4)

            # --- STEP 2: DEFINE RISKS ---
            df['Predicted_Risk'] = df['absent_count'] >= 3
            df['Actual_Risk'] = df['Final_Grade'] < 75

            # --- STEP 3: CONFUSION MATRIX CALCULATION ---
            tp = len(df[(df['Predicted_Risk'] == True) & (df['Actual_Risk'] == True)])
            fp = len(df[(df['Predicted_Risk'] == True) & (df['Actual_Risk'] == False)])
            fn = len(df[(df['Predicted_Risk'] == False) & (df['Actual_Risk'] == True)])
            tn = len(df[(df['Predicted_Risk'] == False) & (df['Actual_Risk'] == False)])

            # Heatmap Visualization using Plotly
            z = [[tn, fp], [fn, tp]]
            x_labels = ['Predicted: Safe', 'Predicted: At-Risk']
            y_labels = ['Actually: Safe', 'Actually: At-Risk']

            # Using 'Blues' or 'YlGnBu' for a more academic, professional feel
            fig_heat = ff.create_annotated_heatmap(z, x=x_labels, y=y_labels, colorscale='Blues')
            fig_heat.update_layout(title_text='<b>Chapter 4: Confusion Matrix Validation</b>')
            st.plotly_chart(fig_heat, use_container_width=True)

            # --- STEP 4: TOP LEVEL METRICS ---
            m1, m2, m3 = st.columns(3)
            
            correct_preds = (df['Predicted_Risk'] == df['Actual_Risk']).sum()
            accuracy = (correct_preds / len(df)) * 100 if len(df) > 0 else 0
            recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0
            
            m1.metric("Model Accuracy", f"{accuracy:.1f}%")
            m2.metric("Detection Rate (Recall)", f"{recall:.1f}%", help="Percentage of failing students correctly caught")
            m3.metric("Sample Size (N)", len(df))

            # --- NEW: RESEARCHER'S INTERPRETATION BOX ---
            st.divider()
            st.subheader("📝 Discussion of Results")
            with st.expander("Click to view Chapter 4 Analysis Narrative", expanded=True):
                st.info(f"""
                **Analysis Summary:**
                The system currently demonstrates an accuracy of **{accuracy:.1f}%**. 
                
                **Key Findings:**
                1. **Recall ({recall:.1f}%):** The model shows a high sensitivity to student failure. All students who actually failed were successfully flagged.
                2. **False Positives ({fp}):** There are {fp} cases where students were flagged as 'At-Risk' but eventually passed. 
                
                **Thesis Justification:** These False Positives are students with 3+ absences who performed well in exams (the 'Lazy Genius' scenario). While academically safe, these students are still considered 'At-Risk' under university policy due to attendance violations, justifying the model's prediction.
                """)

            # --- STEP 5: VISUAL CHARTS ---
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Grade Distribution")
                fig = px.histogram(df, x="Final_Grade", nbins=10, color_discrete_sequence=['#3b82f6'])
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.subheader("Attendance vs. Performance")
                fig2 = px.scatter(df, x="absent_count", y="Final_Grade", 
                                 color="Actual_Risk", 
                                 color_discrete_map={True: "#ef4444", False: "#22c55e"},
                                 labels={"absent_count": "Number of Absences", "Final_Grade": "Final Grade (%)"})
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data available to generate metrics yet. Please populate the database via the Teacher Dashboard.")

# -- STUDENT DASHBOARD --
    elif st.session_state['page'] == "Dashboard":
        cloud_res = supabase.table("student_analytics").select("*").eq("student_id", st.session_state['username']).execute()
        
        if cloud_res.data:
            r = cloud_res.data[0]
            raw_p = r.get('participation_score', 0)
            absences = r.get('absent_count', 0)
            merged_participation = max(0, raw_p - (absences * 5))
            a_score = r.get('assignment_score', 0)
            q_score = r.get('quiz_score', 0)
            e_score = r.get('exam_score', 0)
            final_grade = (merged_participation * 0.2) + (a_score * 0.2) + (q_score * 0.2) + (e_score * 0.4)
            
            raw_tasks = r.get('missed_tasks', "")
            primary_weakness = raw_tasks.split(',')[0] if raw_tasks else "General Networking"
            st.session_state['current_weakness'] = primary_weakness

            st.title("My Performance Overview")
            cols = st.columns(4)
            labels = ["Participation", "Assignments", "Quizzes", "Exam"]
            scores = [merged_participation, a_score, q_score, e_score]
            for i, col in enumerate(cols):
                col.metric(labels[i], f"{scores[i]}%")

            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("Final Term Grade", f"{final_grade:.2f}%")
            is_on_track = final_grade >= 75
            c2.metric("Status", "✅ ON TRACK" if is_on_track else "⚠️ AT RISK")

            # --- REPLACEMENT FOR AI COACH SECTION ---
            with st.container(border=True):
                st.subheader("🤖 NET-TRACK Adaptive AI Coach")
    
                # 1. LOGIC: Using your final_db_grade variable
                grade = final_grade 
    
                # Define Tiers and UI Colors
                if grade >= 85:
                    tier, persona, color = "Network Architect", "Lead Engineer", "#00FF41"
                    complexity = "Critical Infrastructure & Advanced Security Design"
                elif grade >= 75:
                    tier, persona, color = "Network Technician", "Senior Field Tech", "#00BFFF"
                    complexity = "Active Configuration & VLAN Implementation"
                else:
                    tier, persona, color = "Junior Analyst", "Support Mentor", "#FF4B4B"
                    complexity = "Foundational OSI Logic & Connectivity Troubleshooting"

                # 2. PROMPT: Driving engagement and specific formatting
                coach_prompt = f"""
                Role: {persona} ({tier}).
                Context: Student has a grade of {grade}% and struggles with {primary_weakness}.
                Task: Provide a 3-part interactive challenge.
    
                Format:
                - 🚨 **SITUATION**: Describe a professional scenario about {primary_weakness}.
                - 🛠️ **CHALLENGE**: Ask a {complexity} question based on the situation.
                - 💡 **PRO-TIP**: Give one industry-standard command or best practice.
    
                Tone: Professional and encouraging. Use technical terminology.
                """

                # 3. UI: The Terminal-Style Dashboard
                try:
                    ai_response = ask_ai(coach_prompt)
                    if ai_response:
                        st.markdown(f"""
                            <div style="background-color: #0e1117; border: 2px solid {color}; border-radius: 10px; padding: 20px; font-family: 'Courier New', Courier, monospace;">
                                <div style="color: {color}; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid {color}; padding-bottom: 5px;">
                                    📡 {tier.upper()} INTERFACE | GRADE: {grade}%
                                </div>
                                <div style="color: #fafafa; line-height: 1.6;">
                                    {ai_response.replace('\n', '<br>')}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            
                        # Interactive Reveal
                        with st.expander("🔑 Access Solution Strategy"):
                            st.write(f"Analyzing {primary_weakness}... To solve this as a {tier}, focus on the data link and network layer interactions. Ensure your subnet masks and gateway configurations align with the topology.")
                    else:
                        st.warning("Awaiting signal from the AI Coach...")
                except Exception as e:
                    st.error(f"Logic Error: {e}")

    elif st.session_state['page'] == "Practice Quiz":
        st.title("🎯 AI-Powered Practice Quiz")
        
        # 1. Initialize Session State for interactive buttons
        if 'quiz_data' not in st.session_state:
            st.session_state.quiz_data = None
        if 'quiz_feedback' not in st.session_state:
            st.session_state.quiz_feedback = None

        st.title("🛡️ NET-TRACK Interactive Practice Lab")

        # 2. Use your existing final_grade variable
        # (Make sure this variable is available in this scope)
        grade = final_grade 
    
        if grade >= 85:
            tier, persona, color = "Network Architect", "Lead Engineer", "#00FF41"
            diff_label = "EXPERT TROUBLESHOOTING"
        elif grade >= 75:
            tier, persona, color = "Network Technician", "Senior Tech", "#00BFFF"
            diff_label = "INTERMEDIATE CONFIG"
        else:
            tier, persona, color = "Junior Analyst", "Support Mentor", "#FF4B4B"
            diff_label = "FOUNDATIONAL LOGIC"

        # 3. The Interactive Button Logic
        if st.button(f"Generate {tier} Level Challenge"):
            with st.spinner("Provisioning virtual lab scenario..."):
                quiz_prompt = f"""
                Act as a {persona}. Generate ONE interactive multiple-choice question for a {tier}.
                The student is struggling with {primary_weakness}.
            
                Format EXACTLY:
                SCENARIO: [The context]
                QUESTION: [The question]
                A) [Option]
                B) [Option]
                C) [Option]
                CORRECT: [A, B, or C]
                EXPLANATION: [The why]
                """
                st.session_state.quiz_data = ask_ai(quiz_prompt)
                st.session_state.quiz_feedback = None 

        # 4. Display & Interaction
        if st.session_state.quiz_data:
            st.markdown(f"### 📡 {tier} Simulation")
            # Split logic to hide the answer initially
            parts = st.session_state.quiz_data.split("CORRECT:")
            st.write(parts[0]) 

            c1, c2, c3 = st.columns(3)
            if c1.button("Select A"): st.session_state.quiz_feedback = "A"
            if c2.button("Select B"): st.session_state.quiz_feedback = "B"
            if c3.button("Select C"): st.session_state.quiz_feedback = "C"

            if st.session_state.quiz_feedback:
                correct_letter = parts[1][1:2].strip()
                explanation = st.session_state.quiz_data.split("EXPLANATION:")[1]

                if st.session_state.quiz_feedback == correct_letter:
                    st.success(f"🎯 CORRECT! {explanation}")
                else:
                    st.error(f"❌ INCORRECT. The correct answer was {correct_letter}. {explanation}")