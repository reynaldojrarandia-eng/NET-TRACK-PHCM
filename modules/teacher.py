import streamlit as st
import pandas as pd
import openpyxl
import time
from rapidfuzz import process, utils

def render_teacher_dashboard(supabase):
    st.title("👨‍🏫 Faculty Grade Management")
    res = supabase.table("student_analytics").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data).drop_duplicates(subset=['student_id'])
        
        st.subheader("📊 Class Insights")
        m1, m2, m3, m4 = st.columns(4)

        avg_grade = df['total_weighted_grade'].mean()
        avg_absent = df['absent_count'].mean()
        avg_participation = df['participation_score'].mean()
        at_risk = df[(df['absent_count'] >= 3) | (df['total_weighted_grade'] < 75)].shape[0]
        
        m1.metric("Avg. Absences", f"{avg_absent:.1f}", delta="-0.2", delta_color="inverse")
        m2.metric("Avg. Participation", f"{avg_participation:.1f}%")
        m3.metric("At-Risk Students", at_risk, delta=f"{at_risk}", delta_color="inverse")
        m4.metric("Total Students", len(df))
        st.divider()

        with st.expander("📂 Import Attendance from Excel (Advanced Matching)", expanded=False):
            st.write("Upload a sheet with student names. The AI will match them to your registered users.")
            att_file = st.file_uploader("Choose Attendance Excel", type=["xlsx"])

            if att_file:
                prof_res = supabase.table("profiles").select("username, full_name").eq("role", "Student").execute()
                db_students = {s['full_name']: s['username'] for s in prof_res.data}

                wb = openpyxl.load_workbook(att_file, data_only=True)
                ws = wb.active

                match_results = []
                for row in ws.iter_rows(min_row=2):
                    excel_name = row[0].value
                    if not excel_name: continue

                    match = process.extractOne(
                        str(excel_name), db_students.keys(), processor=utils.default_process, score_cutoff=90
                    )

                    if match:
                        matched_name, score, _ = match
                        student_id = db_students[matched_name]

                        date_cells = row[1:5]
                        total_possible_sessions = len(date_cells)
                        absences = 0
                        for cell in date_cells:
                            val = cell.value
                            has_text = val is not None and str(val).strip() != ""
                            if has_text: continue
                            is_yellow = cell.fill.start_color.index in ['FFFFFF00', 6]
                            if is_yellow:
                                absences += 1
                        
                        attended = total_possible_sessions - absences
                        participation_pct = (attended / total_possible_sessions) * 100

                        match_results.append({
                            "Student ID": student_id, "Excel Name": excel_name,
                            "Matched To": matched_name, "Absences Found": absences,
                            "Raw Participation": participation_pct
                        })

                if match_results:
                    match_df = pd.DataFrame(match_results)
                    st.dataframe(match_df)
                    
                    if st.button("Confirm & Bulk Update"):
                        with st.spinner("Processing attendance..."):
                            success_count = 0
                            for item in match_results:
                                response = supabase.table("student_analytics").update({
                                    "absent_count": int(item["Absences Found"]),
                                    "participation_score": float(item["Raw Participation"])
                                }).eq("student_id", item["Student ID"]).execute()

                                if not response.data:
                                    supabase.table("student_analytics").upsert({
                                        "student_id": item["Student ID"], "absent_count": int(item["Absences Found"]),
                                        "participation_score": float(item["Raw Participation"]), "assignment_score": 0,
                                        "quiz_score": 0, "exam_score": 0
                                    }).execute()
                                success_count += 1

                            if success_count > 0:
                                st.toast(f"✅ Synced {success_count} students from Excel!", icon='📊')
                                time.sleep(1)
                                st.success("Attendance successfully integrated.")
                                st.rerun()

        st.subheader("📝 Class Grade Sheet")
        df['participation_score'] = ((4 - df['absent_count']) / 4 * 100).clip(lower=0)
        df['Total Grade (%)'] = (df['participation_score']*0.2) + (df['assignment_score']*0.2) + (df['quiz_score']*0.2) + (df['exam_score']*0.4)

        def get_status(row):
            if row['absent_count'] >= 3: return "🚩 At Risk"
            if row['Total Grade (%)'] < 75: return "⚠️ Low Performance"
            return "✅ Stable"

        df['Status'] = df.apply(get_status, axis=1)
        cols_to_edit = ['Status', 'student_id', 'absent_count', 'Total Grade (%)', 'participation_score', 'assignment_score', 'quiz_score', 'exam_score']

        updated_df = st.data_editor(
            df[cols_to_edit], key="grade_editor_v2",
            column_config={
                "Status": st.column_config.TextColumn("System Status", disabled=True),
                "student_id": st.column_config.TextColumn("Student ID", disabled=True),
                "Total Grade (%)": st.column_config.NumberColumn("Total Grade (%)", format="%.1f", disabled=True),
                "absent_count": st.column_config.NumberColumn("Absences", min_value=0),
                "participation_score": st.column_config.ProgressColumn("Participation", min_value=0, max_value=100, format="%d%%"),
                "assignment_score": st.column_config.NumberColumn("Assignments (20%)", min_value=0, max_value=100),
                "quiz_score": st.column_config.NumberColumn("Quizzes (20%)", min_value=0, max_value=100),
                "exam_score": st.column_config.NumberColumn("Examination (40%)", min_value=0, max_value=100),
            }, hide_index=True, use_container_width=True
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