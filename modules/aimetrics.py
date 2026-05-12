import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score, recall_score

def render_teacher_metrics(supabase):
    st.title("📊 AI Model Performance Analytics")
    st.write("Validation of Predictive Models using an 80/20 Train-Test Validation Split.")
    
    res = supabase.table("student_analytics").select("*").execute()

    if res.data:
        df = pd.DataFrame(res.data)
        
        # 1. Feature Engineering (Matches Teacher Logic)
        df['Final_Grade'] = (df['participation_score']*0.2) + (df['assignment_score']*0.2) + (df['quiz_score']*0.2) + (df['exam_score']*0.4)
        # Actual Risk is the "Label" the AI is trying to guess
        df['Actual_Risk'] = (df['Final_Grade'] < 75) | (df['absent_count'] >= 3)
        
        # 2. Data Preparation
        X = df[['participation_score', 'assignment_score', 'quiz_score', 'exam_score', 'absent_count']]
        y = df['Actual_Risk']
        
        # 3. SCIENTIFIC VALIDATION: Train-Test Split
        # We hide 20% of the students (10 students if N=50) to test the AI
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 4. Model Training (Training on 80% only)
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        
        knn = KNeighborsClassifier(n_neighbors=3)
        knn.fit(X_train, y_train)

        # 5. Model Prediction (Testing on the 20% unseen data)
        rf_test_preds = rf.predict(X_test)
        knn_test_preds = knn.predict(X_test)

        # 6. Metrics Calculation
        rf_acc = accuracy_score(y_test, rf_test_preds) * 100
        knn_acc = accuracy_score(y_test, knn_test_preds) * 100
        rf_recall = recall_score(y_test, rf_test_preds) * 100

        # 7. Confusion Matrix Visualization
        st.subheader("Chapter 4: Confusion Matrix (Testing on Unseen Data)")
        tab1, tab2 = st.tabs(["Random Forest (Predictive)", "K-Nearest Neighbors"])
        
        with tab1:
            cm_rf = confusion_matrix(y_test, rf_test_preds)
            fig_rf = ff.create_annotated_heatmap(
                cm_rf.tolist(), 
                x=['Pred: Safe', 'Pred: At-Risk'], 
                y=['Actually: Safe', 'Actually: At-Risk'], 
                colorscale='Blues'
            )
            fig_rf.update_layout(height=400)
            st.plotly_chart(fig_rf, use_container_width=True)
            
        with tab2:
            cm_knn = confusion_matrix(y_test, knn_test_preds)
            fig_knn = ff.create_annotated_heatmap(
                cm_knn.tolist(), 
                x=['Pred: Safe', 'Pred: At-Risk'], 
                y=['Actually: Safe', 'Actually: At-Risk'], 
                colorscale='Greens'
            )
            fig_knn.update_layout(height=400)
            st.plotly_chart(fig_knn, use_container_width=True)

        # 8. Comparison Dashboard
        st.divider()
        st.subheader("📈 Model Efficiency Comparison")
        m1, m2, m3 = st.columns(3)
        
        m1.metric("Random Forest Accuracy", f"{rf_acc:.1f}%")
        m2.metric("KNN Accuracy", f"{knn_acc:.1f}%", delta=f"{knn_acc - rf_acc:.1f}% vs RF")
        m3.metric("Sample Size (N)", len(df), help="Total students currently in the database.")

        st.divider()
        st.subheader("📝 Discussion of Results")
        with st.expander("Click to view Chapter 4 Analysis Narrative", expanded=True):
            st.info(f"""
            **Analysis Summary:**
            By implementing a Train-Test split, we ensure the model generalizes to new student profiles. 
            The Random Forest demonstrates an accuracy of **{rf_acc:.1f}%** on previously unseen student data.

            **Key Findings:**
            1. **Detection Rate:** The model successfully identified {rf_recall:.1f}% of students who were actually at risk.
            2. **Validation:** Evaluating on a hold-out test set (20% of N={len(df)}) prevents overfitting and provides a reliable metric for university deployment.
            """)
            
        # 9. Original Charts
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Grade Distribution")
            fig = px.histogram(df, x="Final_Grade", nbins=10, color_discrete_sequence=['#3b82f6'])
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Attendance vs. Performance")
            fig2 = px.scatter(df, x="absent_count", y="Final_Grade",
                              color="Actual_Risk",
                              color_discrete_map={True: "#ef4444", False: "#22c55e"},
                              labels={"absent_count": "Absences", "Final_Grade": "Grade (%)"})
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available to generate metrics yet.")