import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, recall_score

def render_teacher_metrics(supabase):
    st.title("📊 AI Model Performance Analytics")
    st.write("Comparative Analysis: Random Forest (Tree-Based) vs. KNN (Distance-Based).")
    
    res = supabase.table("student_analytics").select("*").execute()

    if res.data:
        df = pd.DataFrame(res.data)
        
        # 1. Feature Engineering
        df['Final_Grade'] = (df['participation_score']*0.2) + (df['assignment_score']*0.2) + (df['quiz_score']*0.2) + (df['exam_score']*0.4)
        df['Actual_Risk'] = df['Final_Grade'] < 75
        
        # 2. Prepare Data for AI Training
        # Using scores and absences as features
        X = df[['participation_score', 'assignment_score', 'quiz_score', 'exam_score', 'absent_count']]
        y = df['Actual_Risk']
        
        # 3. Initialize and Fit the 2 Models
        # Model A: Random Forest (The "Leader")
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        df['RF_Pred'] = rf.predict(X)
        
        # Model B: KNN (The "Comparison")
        knn = KNeighborsClassifier(n_neighbors=3)
        knn.fit(X, y)
        df['KNN_Pred'] = knn.predict(X)

        # 4. Confusion Matrix Comparison (Tabs)
        st.subheader("Chapter 4: Confusion Matrix Validation")
        tab1, tab2 = st.tabs(["Random Forest Model", "K-Nearest Neighbors"])
        
        def create_matrix_chart(preds):
            cm = confusion_matrix(df['Actual_Risk'], preds)
            # Ensure 2x2 matrix shape for heatmap even if data is small
            z = cm.tolist() if cm.size == 4 else [[len(df), 0], [0, 0]]
            x_labels = ['Predicted: Safe', 'Predicted: At-Risk']
            y_labels = ['Actually: Safe', 'Actually: At-Risk']
            return ff.create_annotated_heatmap(z, x=x_labels, y=y_labels, colorscale='Blues')

        with tab1:
            st.plotly_chart(create_matrix_chart(df['RF_Pred']), use_container_width=True)
        with tab2:
            st.plotly_chart(create_matrix_chart(df['KNN_Pred']), use_container_width=True)

        # 5. Side-by-Side Efficiency Metrics
        st.divider()
        st.subheader("📈 Efficiency Comparison")
        
        col_rf, col_knn = st.columns(2)
        
        # RF Metrics
        rf_acc = accuracy_score(df['Actual_Risk'], df['RF_Pred']) * 100
        rf_rec = recall_score(df['Actual_Risk'], df['RF_Pred']) * 100
        with col_rf:
            st.metric("Random Forest Accuracy", f"{rf_acc:.1f}%", delta=f"{rf_rec:.1f}% Recall")
            st.caption("Algorithm: Ensemble Decision Trees")

        # KNN Metrics
        knn_acc = accuracy_score(df['Actual_Risk'], df['KNN_Pred']) * 100
        knn_rec = recall_score(df['Actual_Risk'], df['KNN_Pred']) * 100
        with col_knn:
            diff = knn_acc - rf_acc
            st.metric("KNN Accuracy", f"{knn_acc:.1f}%", delta=f"{diff:.1f}% vs RF", delta_color="normal")
            st.caption("Algorithm: Euclidean Distance Clustering")

        # 6. Narrative Discussion
        st.divider()
        st.subheader("📝 Discussion of Results")
        with st.expander("Click to view Chapter 4 Analysis Narrative", expanded=True):
            st.info(f"""
            **Comparison Summary:**
            The system currently utilizes **Random Forest** as the primary predictor due to its **{rf_acc:.1f}%** accuracy. 
            
            **Key Technical Insights:**
            1. **Random Forest:** Handles non-linear student data by creating multiple decision paths. It is less sensitive to 'outlier' students.
            2. **KNN:** Predicts risk by finding students with similar 'Distance' in their grade profiles. It is highly effective for smaller, localized datasets.
            """)
            
        # 7. Distribution Charts
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Grade Distribution")
            fig = px.histogram(df, x="Final_Grade", nbins=10, color_discrete_sequence=['#3b82f6'])
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Attendance vs. Performance")
            fig2 = px.scatter(df, x="absent_count", y="Final_Grade",
                              color="Actual_Risk",
                              color_discrete_map={True: "#ef4444", False: "#22c55e"})
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available to generate metrics yet.")