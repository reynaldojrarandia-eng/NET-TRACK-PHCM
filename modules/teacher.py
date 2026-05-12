import streamlit as st
import pandas as pd
import openpyxl
import time
import io
from rapidfuzz import process, utils

def render_teacher_dashboard(supabase):
    st.title("👨‍🏫 Faculty Grade Management")
    
    # 1. Fetch Data
    res = supabase.table("student_analytics").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data).drop_duplicates(subset=['student_id'])
        
        # Consistent Status Logic for Thesis Accuracy
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

        # 2. Metrics Header (Restored with Deltas)
        st.subheader("📊 Class Insights")
        m1, m2, m3, m4 = st.columns(4)
        
        avg_grade = df['total_weighted_grade'].mean()
        avg_absent = df['absent_count'].mean()
        avg_participation = df['participation_score'].mean()
        at_risk_count = df[df['Status'] == "🚩 At Risk"].shape[0]
        
        m1.metric("Avg. Absences", f"{avg_absent:.1f}", delta="-0.2", delta_color="inverse")
        m2.metric("Avg. Participation", f"{avg_participation:.1f}%", delta="5.2%")
        m3.metric("At-Risk Students", at_risk_count, delta="Checked", delta_color="off")
        m4.metric("Total Students", len(df))
        
        st.divider()
        
        # 3. Search Bar
        search_query = st.text_input("🔍 Search Student ID or Name", placeholder="Type to filter...")
        display_df = df.copy()
        if search_query:
            display_df = df[df['student_id'].str.contains(search_query, case=False)]

        # 4. Main Data Editor
        st.subheader("📋 Student Masterlist")
        edited_df = st.data_editor(
            display_df[['Status', 'student_id', 'absent_count', 'total_weighted_grade', 'participation_score', 'assignment_score', 'quiz_score', 'exam_score']], 
            use_container_width=True,
            hide_index=True,
            key="main_table_editor"
        )

        # 5. Action Buttons (Save & Download)
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Save Changes to Database"):
                with st.spinner("Syncing..."):
                    for _, row in edited_df.iterrows():
                        supabase.table("student_analytics").update({
                            "absent_count": row['absent_count'],
                            "participation_score": row['participation_score'],
                            "assignment_score": row['assignment_score'],
                            "quiz_score": row['quiz_score'],
                            "exam_score": row['exam_score']
                        }).eq("student_id", row['student_id']).execute()
                    st.success("Changes Saved!")
                    time.sleep(1)
                    st.rerun()

        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Grades')
            st.download_button(
                label="📥 Download Grade Report (Excel)",
                data=output.getvalue(),
                file_name="student_grade_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # 6. Bulk Update Section
    st.divider()
    st.subheader("📂 Bulk Update Grades")
    uploaded_file = st.file_uploader("Upload Excel/CSV Template", type=['xlsx', 'csv'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                input_df = pd.read_excel(uploaded_file)
            else:
                input_df = pd.read_csv(uploaded_file)
            
            st.write("Preview:")
            st.dataframe(input_df.head(), use_container_width=True)

            if st.button("Confirm and Sync to Supabase"):
                with st.spinner("Processing..."):
                    updates = []
                    for _, row in input_df.iterrows():
                        p = row.get('participation_score', 0)
                        a = row.get('assignment_score', 0)
                        q = row.get('quiz_score', 0)
                        e = row.get('exam_score', 0)
                        calc = (p*0.2) + (a*0.2) + (q*0.2) + (e*0.4)
                        
                        updates.append({
                            "student_id": row['student_id'],
                            "absent_count": row.get('absent_count', 0),
                            "participation_score": p,
                            "assignment_score": a,
                            "quiz_score": q,
                            "exam_score": e,
                            "total_weighted_grade": round(calc, 2)
                        })
                    supabase.table("student_analytics").upsert(updates, on_conflict="student_id").execute()
                    st.success("Bulk update successful!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error processing file: {e}")