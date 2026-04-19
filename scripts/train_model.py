import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 1. LOAD DATA
data = pd.read_csv('../datasets/student_data.csv')
X = data[['lab_completion_time', 'accuracy_score', 'attempts']]
y = data['status']

# 2. TUNED RANDOM FOREST (Making it "Strict" / Overfitting)
# By setting max_depth=2, we force the trees to be very simple and biased.
rf_model = RandomForestClassifier(n_estimators=100, max_depth=2, random_state=42)
rf_model.fit(X, y)

# 3. TUNED SVM (Making it "Relaxed")
# Increasing C=10 makes the SVM try harder to classify every point correctly.
svm_model = SVC(kernel='rbf', C=10, gamma=0.001, random_state=42)
svm_model.fit(X, y)

# 4. GENERATE PREDICTIONS
data['RF_Prediction'] = rf_model.predict(X)
data['SVM_Prediction'] = svm_model.predict(X)

# 5. PERFORMANCE REPORT
rf_acc = accuracy_score(y, data['RF_Prediction']) * 100
svm_acc = accuracy_score(y, data['SVM_Prediction']) * 100

print(f"--- NET-TRACK PERFORMANCE ---")
print(f"Random Forest Accuracy: {rf_acc:.2f}%")
print(f"SVM Accuracy: {svm_acc:.2f}%")

# 6. SHOW THE CONFLICTS
disagreements = data[data['RF_Prediction'] != data['SVM_Prediction']]

if not disagreements.empty:
    print("\n--- FOUND MODEL DISAGREEMENTS! ---")
    print(disagreements[['student_id', 'status', 'RF_Prediction', 'SVM_Prediction']])
else:
    print("\nStill no disagreements. The patterns in your data are very strong!")

data.to_csv('../datasets/conflict_results.csv', index=False)

# Add this at the very end of your existing train_model.py
import joblib

# We'll save the Random Forest model since it's usually great for this data
joblib.dump(rf_model, '../models/net_track_rf_model.pkl') 
print("✅ AI Brain saved to models folder!")