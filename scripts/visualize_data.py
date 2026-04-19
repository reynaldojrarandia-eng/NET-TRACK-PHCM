import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.svm import SVC
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 1. LOAD DATA
data = pd.read_csv('../datasets/student_data.csv')
X_vis = data[['lab_completion_time', 'accuracy_score']]
y_vis = data['status'].map({'Pass': 1, 'Fail': 0})

# 2. TRAIN A VISUALIZATION MODEL
model = SVC(kernel='rbf', C=1.0)
model.fit(X_vis, y_vis)

# 3. CREATE BACKGROUND MAP (Meshgrid)
h = .5 
x_min, x_max = X_vis['lab_completion_time'].min() - 10, X_vis['lab_completion_time'].max() + 10
y_min, y_max = X_vis['accuracy_score'].min() - 10, X_vis['accuracy_score'].max() + 10
xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

# 4. PREDICT ZONES
Z = model.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

# 5. PLOTTING
plt.figure(figsize=(10, 7))
# Draw the 'territory' (Green for Pass, Red for Fail)
plt.contourf(xx, yy, Z, alpha=0.3, cmap=plt.cm.RdYlGn)

# Draw the actual student points
sns.scatterplot(data=data, x='lab_completion_time', y='accuracy_score', 
                hue='status', style='status', s=100, 
                palette={'Pass': 'green', 'Fail': 'red'}, edgecolor='black')

plt.title('NET-TRACK: AI Decision Boundary (SVM)', fontsize=15)
plt.xlabel('Lab Completion Time (Minutes)')
plt.ylabel('Accuracy Score (%)')
plt.savefig('../decision_boundary_chart.png')
print("--- BOUNDARY CHART GENERATED ---")
plt.show()