import streamlit as st
import random
import json
from utils.ai_handler import ask_ai

def render_practice_quiz(final_grade, primary_weakness):
    if 'quiz_batch' not in st.session_state: st.session_state.quiz_batch = []
    if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
    if 'quiz_submitted' not in st.session_state: st.session_state.quiz_submitted = False
    if 'batch_id' not in st.session_state: st.session_state.batch_id = random.randint(1000, 9999)
    if 'current_mode' not in st.session_state: st.session_state.current_mode = "MCQ"
    
    color = "#4ade80" if final_grade >= 85 else "#60a5fa" if final_grade >= 75 else "#f87171"
    glow = "rgba(74, 222, 128, 0.2)" if final_grade >= 85 else "rgba(96, 165, 250, 0.2)"
    tier_name = "Network Architect" if final_grade >= 85 else "Network Technician" if final_grade >= 75 else "Junior Analyst"
    
    st.title("🛡️ NET-TRACK Advanced Practice Lab")
    st.caption(f"Authenticated as: {tier_name} | Targeting: {primary_weakness}")
    
    if st.button(f"🚀 Deploy {tier_name} Assessment Batch", use_container_width=True):
        st.session_state.current_mode = random.choice(["MCQ", "Identification", "Essay"])
        st.session_state.quiz_submitted = False
        st.session_state.batch_id = random.randint(1000, 9999)
        
        with st.spinner(f"🧠 Synthesizing {st.session_state.current_mode} scenarios..."):
            quiz_prompt = f"""
            Act as a Senior Network Proctor. Generate 10 UNIQUE modules (but for essay mode make it only 3 Modules) of type: {st.session_state.current_mode}.
            Topic Focus: {primary_weakness}.
            STRICT QUALITY REQUIREMENTS:
            - SCENARIO: Must be a complex 'Field Report'. Include symptoms, error codes, or specific architecture constraints.
            - QUESTION: Do not ask for definitions. Ask for 'Diagnostic Identification' or 'Architectural Decisions'.
            - IDENTIFICATION: Provide both 'correct_full' (Formal name) and 'correct_short' (Acronym).
            - DIVERSITY: Ensure each of the 10 questions (but for essay mode make it only 3 questions) uses a different context (e.g., Security, Cloud, Hardware).
            - ESSAY: For this mode Ensure it only has 3 Modules/Questions!
            - ADDITONALLY: FOR ESSAY MODE MAKE IT ONLY 3 MODULES, BUT FOR MCQ AND IDENTIFICATION MAKE IT 10 MODULES!!
            Return ONLY a JSON list:
            [{{
                "scenario": "...", "question": "...", "options": ["A) ...", "B) ...", "C) ..."],
                "correct_full": "...", "correct_short": "...", "explanation": "..."
            }}]
            """
            raw_response = ask_ai(quiz_prompt)
            try:
                start = raw_response.find('[')
                end = raw_response.rfind(']') + 1
                st.session_state.quiz_batch = json.loads(raw_response[start:end])
                st.session_state.user_answers = {}
            except:
                st.error("AI Logic Desync. Please try deploying again.")
                
    if st.session_state.quiz_batch:
        st.markdown(f"<h4 style='color:{color}; text-align:center;'>--- {st.session_state.current_mode.upper()} MODE ACTIVE ---</h4>", unsafe_allow_html=True)

        for i, q in enumerate(st.session_state.quiz_batch):
            u_key = f"lab_{st.session_state.batch_id}_{i}"
            st.markdown(f"""
            <div style="background-color: rgba(128, 128, 128, 0.05); border: 1px solid {color}; border-left: 8px solid {color};
            box-shadow: 0px 4px 15px {glow}; padding: 20px; border-radius: 10px; margin-top: 25px; margin-bottom: 10px;">
                <span style="color: {color}; font-weight: bold; font-family: monospace;">[ MODULE {i+1} ]</span><br><br>
                <b>FIELD REPORT:</b><br>{q.get('scenario', 'Analyzing node...')}<br><br>
                <b style="color: {color};">PROCTOR'S INQUIRY:</b><br>{q.get('question', 'Identify the anomaly.')}
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.current_mode == "MCQ":
                st.session_state.user_answers[i] = st.radio("Select Response:", q.get('options', []), key=u_key)
            elif st.session_state.current_mode == "Identification":
                st.session_state.user_answers[i] = st.text_input("Technical Entry:", key=u_key, placeholder="Enter protocol name or acronym...")
            elif st.session_state.current_mode == "Essay":
                st.session_state.user_answers[i] = st.text_area("Analysis Report:", key=u_key, placeholder="Detailed engineering breakdown...")
                
        if st.button("EXECUTE BATCH EVALUATION", type="primary", use_container_width=True):
            st.session_state.quiz_submitted = True
            
        if st.session_state.quiz_submitted:
            st.divider()
            for i, q in enumerate(st.session_state.quiz_batch):
                user_ans = str(st.session_state.user_answers.get(i, "")).strip()
                with st.expander(f"Review Module {i+1} Results", expanded=True):
                    if st.session_state.current_mode == "MCQ":
                        target = str(q.get('correct_short', q.get('correct_full', 'A'))).upper()
                        if user_ans.upper().startswith(target[0]):
                            st.success(f"✅ **Signal Match:** {q.get('explanation')}")
                        else:
                            st.error(f"❌ **Mismatch:** Expected {target}. {q.get('explanation')}")
                    elif st.session_state.current_mode == "Identification":
                        u_clean = user_ans.lower().replace(" ", "")
                        t_full = str(q.get('correct_full', '')).lower().replace(" ", "")
                        t_short = str(q.get('correct_short', '')).lower().replace(" ", "")
                        if (u_clean == t_full or u_clean == t_short or (len(u_clean) > 3 and u_clean in t_full)):
                            st.success(f"✅ **Validated:** {q.get('correct_full')} ({q.get('correct_short')})")
                            st.write(f"*Analysis: {q.get('explanation')}*")
                        else:
                            st.error(f"❌ **Identity Mismatch**")
                            st.write(f"**Expected:** {q.get('correct_full')} / {q.get('correct_short')}")
                            st.info(f"**Debrief:** {q.get('explanation')}")
                    elif st.session_state.current_mode == "Essay":
                        st.info("📝 **Professional Evaluation Criteria:**")
                        st.write(q.get('explanation', 'Criteria not found.'))