import streamlit as st
from utils.db import get_supabase
from utils.style import apply_custom_design, render_header
from modules import auth 
import modules.teacher as teacher      
import modules.aimetrics as aimetrics    
import modules.student as student    
import modules.quiz_engine as quiz_engine

# --- 1. CONFIG & CONNECTION ---
st.set_page_config(page_title="PERPY: CORE | PHCM", page_icon="🎓", layout="wide")
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
        'current_weakness': "General Theory"
    })

# --- 3. AUTHENTICATION FLOW ---
if not st.session_state['logged_in']:
    auth.render_auth(supabase)
else:
    # --- 4. SIDEBAR (User Profile & Admin Only) ---
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state['username']}")
        st.caption(f"Access Level: {st.session_state['user_role']}")
        st.divider()
        
        # Student Data Background Fetch (Invisible logic)
        final_grade = 0
        primary_weakness = "General Theory"
        if st.session_state['user_role'] == "Student":
            try:
                res = supabase.table("student_analytics").select("*").eq("student_id", st.session_state['username']).execute()
                if res.data:
                    r = res.data[0]
                    raw_p, a_score = r.get('participation_score', 0), r.get('assignment_score', 0)
                    q_score, e_score = r.get('quiz_score', 0), r.get('exam_score', 0)
                    
                    final_grade = (raw_p * 0.2) + (a_score * 0.2) + (q_score * 0.2) + (e_score * 0.4)
                    st.session_state['final_grade'] = final_grade
                    
                    scores = {"Participation": raw_p, "Assignments": a_score, "Quizzes": q_score, "Exam": e_score}
                    primary_weakness = min(scores, key=scores.get)
                    st.session_state['current_weakness'] = primary_weakness
            except Exception:
                pass

        if st.button("Log Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- 5. MAIN INTERFACE & ROUTING ---
    if st.session_state['user_role'] == "Teacher":
        render_header("Teacher Console", "Academic Performance & Data Management")
        
        # Horizontal Tabs for Teachers
        t1, t2 = st.tabs(["📊 Teacher Dashboard", "🧠 AI Model Metrics"])
        
        with t1:
            teacher.render_teacher_dashboard(supabase)
        with t2:
            aimetrics.render_teacher_metrics(supabase)
            
    else:
        render_header("Student Portal", "Adaptive Learning & Growth Analysis")
        
        # Horizontal Tabs for Students
        t1, t2 = st.tabs(["🏠 Dashboard", "📝 Practice Quiz"])
        
        with t1:
            student.render_student_dashboard(supabase)
        with t2:
            # Grabbing fresh data from session state
            fg = st.session_state.get('final_grade', 0)
            pw = st.session_state.get('current_weakness', "Core Concepts")
            quiz_engine.render_practice_quiz(fg, pw)