import json
import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier

# 1. Load your collected data
data_filename = 'goal_training_data.json'

if not os.path.exists(data_filename):
    print(f"❌ Error: '{data_filename}' not found. Please play the game first to generate data.")
    exit()

with open(data_filename, 'r') as f:
    data = json.load(f)

# Convert list of dictionaries to DataFrame
df = pd.DataFrame(data)
print(f"✅ Loaded {len(df)} game records for training.")

# 2. Define Features (Inputs from the first 6 months)
feature_cols = [
    'early_avg_happiness',
    'early_avg_stress',
    'early_total_investments',
    'early_total_saved',
    'early_total_debt_paid',
    'early_num_leisure',
    'early_num_risky'
]

# 3. Define Targets (The 4 goals you want to predict)
target_cols = [
    'goal_networth', 
    'goal_emergency', 
    'goal_debtfree', 
    'goal_happiness'
]

# 4. Prepare Data
X = df[feature_cols]
y = df[target_cols]

# 5. Train the Model
# n_estimators=100 is good for stability
base_model = RandomForestClassifier(n_estimators=100, random_state=42)
model = MultiOutputClassifier(base_model)
model.fit(X, y)

# 6. Save the trained model and feature list
joblib.dump(model, 'goal_predictor.pkl')
joblib.dump(feature_cols, 'goal_features.pkl')

print("🚀 Success! 'goal_predictor.pkl' has been created.")
print("You can now run your game and use the 'PREDICT GOALS' button.")