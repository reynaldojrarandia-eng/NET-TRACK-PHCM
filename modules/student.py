import streamlit as st
from utils.ai_handler import ask_ai

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
                complexity = "Critical Infrastructure & Advanced Security Design"
            elif grade >= 75:
                tier, persona, color = "Network Technician", "Senior Field Tech", "#00BFFF"
                complexity = "Active Configuration & VLAN Implementation"
            else:
                tier, persona, color = "Junior Analyst", "Support Mentor", "#FF4B4B"
                complexity = "Foundational OSI Logic & Connectivity Troubleshooting"
                
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

                    with st.expander("🔑 Access Solution Strategy"):
                        st.write(f"Analyzing {primary_weakness}... To solve this as a {tier}, focus on the data link and network layer interactions. Ensure your subnet masks and gateway configurations align with the topology.")
                else:
                    st.warning("Awaiting signal from the AI Coach...")
            except Exception as e:
                st.error(f"Logic Error: {e}")