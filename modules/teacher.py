import streamlit as st
import pandas as pd
import openpyxl
import time
from rapidfuzz import process, utils

def render_teacher_dashboard(supabase):
    st.title(" 👨‍🏫  Faculty Grade Management")
    
    # 1. Fetch Data
    res = supabase.table("student_analytics").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data).drop_duplicates(subset=['student_id'])
        
        # Status Logic Fix: Grade < 75 OR Absences >= 3
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

        # 2. TOP METRICS (Original 4-column layout)
        st.subheader(" 📊  Class Insights")
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

        # 3. SEARCH BAR
        search_query = st.text_input("🔍 Search Student ID or Name", "")
        display_df = df.copy()
        if search_query:
            display_df = df[df['student_id'].str.contains(search_query, case=False)]

        # 4. STUDENT MASTERLIST (Restored Participation Bar)
        st.subheader("📝 Class Grade Sheet")
        updated_df = st.data_editor(
            display_df[['Status', 'student_id', 'absent_count', 'total_weighted_grade', 'participation_score', 'assignment_score', 'quiz_score', 'exam_score']], 
            column_config={
                "participation_score": st.column_config.ProgressColumn(
                    "Participation Score",
                    help="Visual tracking of engagement",
                    format="%f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
            use_container_width=True,
            hide_index=True,
            key="teacher_table_v_original"
        )

        if st.button("Save Changes to Database 🔄", type="primary", use_container_width=True):
            if updated_df is not None:
                with st.spinner("🚀 Synchronizing with Supabase..."):
                    updates = []
                    
                    for index, row in updated_df.iterrows():
                        p_score = float(row['participation_score'])
                        a_score = float(row['assignment_score'])
                        q_score = float(row['quiz_score'])
                        e_score = float(row['exam_score'])
                        
                        calc_grade = (p_score * 0.2) + (a_score * 0.2) + (q_score * 0.2) + (e_score * 0.4)
                        
                        updates.append({
                            "student_id": str(row['student_id']),
                            "absent_count": int(row['absent_count']),
                            "participation_score": p_score,
                            "assignment_score": a_score,
                            "quiz_score": q_score,
                            "exam_score": e_score,
                            "total_weighted_grade": round(calc_grade, 2)
                        })

                    try:
                        result = supabase.table("student_analytics").upsert(updates, on_conflict="student_id").execute()
                        
                        if result.data:
                            st.cache_data.clear() 
                            st.success(f"✅ Database Updated! {len(result.data)} rows modified.")
                            time.sleep(1)
                            st.rerun() 
                        else:
                            st.error("⚠️ Supabase accepted the request but no data was changed.")
                    except Exception as e:
                        st.error(f"❌ Sync failed: {str(e)}")
            else:
                st.warning("No changes detected in the editor.")

        st.divider()
        st.subheader("📄 Export Report")
        st.write("Download the current grade records for official university documentation.")
        export_df = df.copy()
        csv_data = export_df.to_csv(index=False).encode('utf-8-sig')

        st.download_button(
            label="📥 Download Grade Report (CSV)",
            data=csv_data,
            file_name=f'NETTRACK_Grades_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )