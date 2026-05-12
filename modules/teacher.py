import streamlit as st
import pandas as pd
import openpyxl
import time
from rapidfuzz import process, utils

def render_teacher_dashboard(supabase):
    st.title("👨‍🏫 Faculty Grade Management")
    
    # Fetch data
    res = supabase.table("student_analytics").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data).drop_duplicates(subset=['student_id'])
        
        # FIX: Unified Status Logic
        def calculate_status(row):
            grade = row['total_weighted_grade']
            absences = row['absent_count']
            if grade < 75 or absences >= 3:
                return "🚩 At Risk"
            elif 75 <= grade < 80:
                return "⚠️ Low Performance"
            else:
                return "✅ Stable"

        df['Status'] = df.apply(calculate_status, axis=1)

        st.subheader("📊 Class Insights")
        m1, m2, m3, m4 = st.columns(4)
        
        avg_grade = df['total_weighted_grade'].mean()
        avg_absent = df['absent_count'].mean()
        avg_participation = df['participation_score'].mean()
        at_risk_count = df[df['Status'] == "🚩 At Risk"].shape[0]
        
        # Restored your original metrics with deltas
        m1.metric("Avg. Absences", f"{avg_absent:.1f}", delta="-0.2", delta_color="inverse")
        m2.metric("Avg. Participation", f"{avg_participation:.1f}%", delta="5.2%")
        m3.metric("At-Risk Students", at_risk_count, delta="Checked", delta_color="off")
        m4.metric("Total Students", len(df))
        
        st.divider()
        
        st.subheader("📋 Student Masterlist")
        st.dataframe(
            df[['Status', 'student_id', 'absent_count', 'total_weighted_grade', 'participation_score', 'assignment_score', 'quiz_score', 'exam_score']], 
            use_container_width=True,
            hide_index=True
        )

    st.divider()
    st.subheader("📂 Bulk Update Grades")
    uploaded_file = st.file_uploader("Upload Excel/CSV Template", type=['xlsx', 'csv'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                input_df = pd.read_excel(uploaded_file)
            else:
                input_df = pd.read_csv(uploaded_file)
            
            st.write("Preview of Uploaded Data:")
            st.dataframe(input_df.head(), use_container_width=True)

            if st.button("Confirm and Sync to Supabase"):
                with st.spinner("Synchronizing student records..."):
                    updates = []
                    for _, row in input_df.iterrows():
                        p_score = row.get('participation_score', 0)
                        a_score = row.get('assignment_score', 0)
                        q_score = row.get('quiz_score', 0)
                        e_score = row.get('exam_score', 0)
                        calc_grade = (p_score*0.2) + (a_score*0.2) + (q_score*0.2) + (e_score*0.4)
                        
                        updates.append({
                            "student_id": row['student_id'],
                            "absent_count": row.get('absent_count', 0),
                            "participation_score": p_score,
                            "assignment_score": a_score,
                            "quiz_score": q_score,
                            "exam_score": e_score,
                            "total_weighted_grade": round(calc_grade, 2)
                        })
                    
                    result = supabase.table("student_analytics").upsert(updates, on_conflict="student_id").execute()
                    if result.data:
                        st.success(f"Successfully updated {len(result.data)} students!")
                        time.sleep(1)
                        st.rerun()
        except Exception as e:
            st.error(f"Error processing file: {e}")