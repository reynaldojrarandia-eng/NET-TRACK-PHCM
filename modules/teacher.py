import streamlit as st
import pandas as pd
import time
import io

def render_teacher_dashboard(supabase):
    st.title("👨‍🏫 Faculty Grade Management")
    
    res = supabase.table("student_analytics").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data).drop_duplicates(subset=['student_id'])
        
        # Unified Status Logic for Thesis
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

        # Dashboard Metrics
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
        
        # Search and Table
        search_query = st.text_input("🔍 Search Student ID or Name", "")
        if search_query:
            df = df[df['student_id'].str.contains(search_query, case=False)]

        st.subheader("📋 Student Masterlist")
        edited_df = st.data_editor(
            df[['Status', 'student_id', 'absent_count', 'total_weighted_grade', 'participation_score', 'assignment_score', 'quiz_score', 'exam_score']], 
            use_container_width=True,
            hide_index=True,
            key="teacher_editor"
        )

        # RESTORED: Save and Download Buttons
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Save Changes to Database"):
                with st.spinner("Saving..."):
                    # Logic to update database from edited_df
                    for _, row in edited_df.iterrows():
                        supabase.table("student_analytics").update({
                            "absent_count": row['absent_count'],
                            "participation_score": row['participation_score'],
                            "assignment_score": row['assignment_score'],
                            "quiz_score": row['quiz_score'],
                            "exam_score": row['exam_score']
                        }).eq("student_id", row['student_id']).execute()
                    st.success("Database Updated!")
                    time.sleep(1)
                    st.rerun()

        with col2:
            # RESTORED: Download Grade Report
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Grades')
            st.download_button(
                label="📥 Download Grade Report (Excel)",
                data=output.getvalue(),
                file_name="student_grade_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # File Upload Section
    st.divider()
    st.subheader("📂 Bulk Update Grades")
    uploaded_file = st.file_uploader("Upload Excel/CSV Template", type=['xlsx', 'csv'])
    if uploaded_file:
        try:
            input_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            st.dataframe(input_df.head(), use_container_width=True)
            if st.button("Confirm and Sync"):
                updates = []
                for _, row in input_df.iterrows():
                    calc_grade = (row['participation_score']*0.2) + (row['assignment_score']*0.2) + (row['quiz_score']*0.2) + (row['exam_score']*0.4)
                    updates.append({
                        "student_id": row['student_id'],
                        "absent_count": row.get('absent_count', 0),
                        "participation_score": row['participation_score'],
                        "assignment_score": row['assignment_score'],
                        "quiz_score": row['quiz_score'],
                        "exam_score": row['exam_score'],
                        "total_weighted_grade": round(calc_grade, 2)
                    })
                supabase.table("student_analytics").upsert(updates, on_conflict="student_id").execute()
                st.success("Sync Complete!")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")