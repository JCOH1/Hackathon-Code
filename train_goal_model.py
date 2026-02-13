import json
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier

# Load collected data
with open('goal_training_data.json', 'r') as f:
    data = json.load(f)
df = pd.DataFrame(data)

# Features (first 6 months)
feature_cols = [
    'early_avg_happiness',
    'early_avg_stress',
    'early_total_investments',
    'early_total_saved',
    'early_total_debt_paid',
    'early_num_leisure',
    'early_num_risky'
]
X = df[feature_cols]

# Targets (4 goals)
target_cols = ['goal_networth', 'goal_emergency', 'goal_debtfree', 'goal_happiness']
y = df[target_cols]

# Train a multi‑output random forest
base_model = RandomForestClassifier(n_estimators=100, random_state=42)
model = MultiOutputClassifier(base_model)
model.fit(X, y)

# Save the model and feature list
joblib.dump(model, 'goal_predictor.pkl')
joblib.dump(feature_cols, 'goal_features.pkl')

print("Model trained and saved!")