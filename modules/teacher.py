import streamlit as st
import pandas as pd
import time
from rapidfuzz import process, utils

def render_teacher_dashboard(supabase):
    st.title("👨‍🏫 Faculty Grade Management")
    
    res = supabase.table("student_analytics").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data).drop_duplicates(subset=['student_id'])
        
        # RESTORED: Precise Status Logic for Chapter 4 Alignment
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
        
        m1.metric("Avg. Absences", f"{avg_absent:.1f}", delta="-0.2", delta_color="inverse")
        m2.metric("Avg. Participation", f"{avg_participation:.1f}%")
        m3.metric("At-Risk Students", at_risk_count, delta=f"{at_risk_count}", delta_color="inverse")
        m4.metric("Total Students", len(df))
        
        st.divider()
        st.subheader("📋 Student Masterlist")
        st.dataframe(df[['student_id', 'total_weighted_grade', 'absent_count', 'Status']], use_container_width=True)

    st.divider()
    st.subheader("📂 Bulk Update Grades")
    uploaded_file = st.file_uploader("Upload Excel/CSV Template", type=['xlsx', 'csv'])
    
    if uploaded_file:
        try:
            input_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(input_df.head())

            if st.button("Confirm and Sync to Supabase"):
                with st.spinner("Syncing..."):
                    updates = []
                    for _, row in input_df.iterrows():
                        p, a, q, e = row.get('participation_score', 0), row.get('assignment_score', 0), row.get('quiz_score', 0), row.get('exam_score', 0)
                        calc_grade = (p*0.2) + (a*0.2) + (q*0.2) + (e*0.4)
                        updates.append({
                            "student_id": row['student_id'],
                            "absent_count": row.get('absent_count', 0),
                            "participation_score": p, "assignment_score": a, "quiz_score": q, "exam_score": e,
                            "total_weighted_grade": round(calc_grade, 2)
                        })
                    supabase.table("student_analytics").upsert(updates, on_conflict="student_id").execute()
                    st.success("Sync Complete!")
                    time.sleep(1)
                    st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")