import json
import os

filename = 'goal_training_data.json'

# 1. Load existing data if it exists
if os.path.exists(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
else:
    data = []

print(f"📉 Current records: {len(data)}")

# 2. Create "Fake" Winning Data (The "Perfect Player")
# High happiness, low stress, lots of savings/investments -> WINS ALL GOALS
winning_samples = [
    {
        "early_avg_happiness": 95.0,
        "early_avg_stress": 5.0,
        "early_total_investments": 15000,
        "early_total_saved": 5000,
        "early_total_debt_paid": 2000,
        "early_num_leisure": 8,
        "early_num_risky": 0,
        "goal_networth": True,
        "goal_emergency": True,
        "goal_debtfree": True,
        "goal_happiness": True
    },
    {
        "early_avg_happiness": 85.0,
        "early_avg_stress": 15.0,
        "early_total_investments": 12000,
        "early_total_saved": 4000,
        "early_total_debt_paid": 3000,
        "early_num_leisure": 6,
        "early_num_risky": 1,
        "goal_networth": True,
        "goal_emergency": True,
        "goal_debtfree": True,
        "goal_happiness": True
    }
]

# 3. Add 5 copies of these winners to balance the data
for _ in range(5):
    data.extend(winning_samples)

# 4. Save back to file
with open(filename, 'w') as f:
    json.dump(data, f, indent=2)

print(f"✅ Added {len(winning_samples) * 5} winning records!")
print(f"📈 Total records now: {len(data)}")
print("⚠️ NOW RUN 'train_model.py' TO UPDATE THE BRAIN!")