import streamlit as st
from utils.ai_handler import ask_ai
import time

def render_student_dashboard(supabase):
    st.cache_data.clear()
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
        
        # Save to session state so the Quiz Engine can use it
        st.session_state['current_weakness'] = primary_weakness
        st.session_state['final_grade'] = final_grade

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
        
        with st.container(border=True):
            st.subheader("🤖 NET-TRACK Adaptive AI Coach")
            grade = final_grade

            if grade >= 85:
                tier, persona, color = "Network Architect", "Lead Engineer", "#00FF41"
                focus = "Critical Infrastructure & Advanced Security Design"
            elif grade >= 75:
                tier, persona, color = "Network Technician", "Senior Field Tech", "#00BFFF"
                focus = "Active Configuration & VLAN Implementation"
            else:
                tier, persona, color = "Junior Analyst", "Support Mentor", "#FF4B4B"
                focus = "Foundational OSI Logic & Connectivity Troubleshooting"
                
            coach_prompt = f"""
            Role: {persona} ({tier}).
            Objective: Act as a Career Mentor for a student with a {final_grade}% grade.
            Technical Focus: {primary_weakness}.
            
            Please provide the following:
            1. 🔍 **DIAGNOSIS**: Why is {primary_weakness} vital in a {focus} role?
            2. 🛠️ **CHALLENGE**: Give one complex "What If" scenario involving {primary_weakness}.
            3. 📈 **RECOVERY PLAN**: Provide 2 specific study actions to turn this weakness into a strength.
            4. 💡 **COMMAND**: Share one professional Cisco/Linux command related to this.

            Tone: Professional, high-stakes, and encouraging.
            """
            
            if st.button("Consult AI Mentor", use_container_width=True):
                with st.spinner("Analyzing your technical trajectory..."):
                    try:
                        ai_response = ask_ai(coach_prompt)
                        if ai_response:
                            # Terminal Style Box
                            st.markdown(f"""
                            <div style="background-color: #0d1117; border: 1.5px solid {color}; border-radius: 8px; padding: 25px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);">
                                <div style="color: {color}; font-family: 'Courier New'; font-weight: bold; font-size: 1.1em; border-bottom: 1px solid {color}; padding-bottom: 10px; margin-bottom: 15px;">
                                    > SYSTEM_ACCESS: {tier.upper()} INTERFACE <br>
                                    > FOCUS_AREA: {primary_weakness.upper()}
                                </div>
                                <div style="color: #e6edf3; line-height: 1.8; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                                    {ai_response.replace('\n', '<br>')}
                                </div>
                                <div style="margin-top: 20px; font-size: 0.8em; color: {color}; opacity: 0.7; font-family: 'Courier New';">
                                    -- END OF TRANSMISSION --
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            with st.expander("🔑 View Mentor's Study Hint"):
                                st.write(f"To master {primary_weakness}, try simulating a network failure in Cisco Packet Tracer specifically targeting the {focus} phase. Research 'Industry Best Practices' for this topic.")
                        else:
                            st.warning("Connection to the Mentor node timed out.")
                    except Exception as e:
                        st.error(f"Mentor Logic Error: {e}")
    else:
        st.info("No analytics data found. Please complete your first assessment to activate the AI Coach.")