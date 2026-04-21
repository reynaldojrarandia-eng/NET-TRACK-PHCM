import streamlit as st
from utils.db import get_supabase
from utils.style import apply_custom_design
from modules import auth, teacher, aimetrics, student, quiz_engine

# --- 1. CONFIG & CONNECTION ---
st.set_page_config(page_title="NET-TRACK Pro | PHCM", page_icon="🌐", layout="wide")
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

# --- 3. AUTHENTICATION FLOW ---
if not st.session_state['logged_in']:
    auth.render_auth(supabase)
else:
    # --- 4. MAIN SYSTEM VIEW ---
    with st.sidebar:
        st.markdown('<h2 style="color:#4ade80;">NET-TRACK</h2>', unsafe_allow_html=True)
        st.write(f"User: **{st.session_state['username']}** | {st.session_state['user_role']}")
        st.divider()

        if st.session_state['user_role'] == "Teacher":
            nav = ["Teacher Dashboard", "AI Model Metrics"]
        else:
            nav = ["Dashboard", "Practice Quiz"]
            
        page = st.radio("NAVIGATE", nav, key="nav_radio")
        st.session_state['page'] = page
        
        # Original global fetch block for students
        final_grade = 0
        primary_weakness = "General Networking"
        if st.session_state.get('user_role') == "Student" and st.session_state.get('username'):
            try:
                res = supabase.table("student_analytics").select("*").eq("student_id", st.session_state['username']).execute()
                if res.data:
                    r = res.data[0]
                    raw_p = r.get('participation_score', 0)
                    a_score = r.get('assignment_score', 0)
                    q_score = r.get('quiz_score', 0)
                    e_score = r.get('exam_score', 0)
                    final_grade = (raw_p * 0.2) + (a_score * 0.2) + (q_score * 0.2) + (e_score * 0.4)
                    scores = {"Participation": raw_p, "Assignments": a_score, "Quizzes": q_score, "Exam": e_score}
                    primary_weakness = min(scores, key=scores.get)
            except Exception:
                st.sidebar.warning("⚠️ Syncing limited on public link.")
                
        if st.button("Log Out"):
            st.session_state.clear()
            st.rerun()

    # --- 5. ROUTING LOGIC ---
    if st.session_state['user_role'] == "Teacher":
        if st.session_state['page'] == "Teacher Dashboard":
            teacher_dashboard.render_teacher_dashboard(supabase)
        elif st.session_state['page'] == "AI Model Metrics":
            teacher_metrics.render_teacher_metrics(supabase)
    else:
        if st.session_state['page'] == "Dashboard":
            student_dashboard.render_student_dashboard(supabase)
        elif st.session_state['page'] == "Practice Quiz":
            # Pass the values that were either calculated above or inside the student dashboard
            fg = st.session_state.get('final_grade', final_grade)
            pw = st.session_state.get('current_weakness', primary_weakness)
            quiz_engine.render_practice_quiz(fg, pw)