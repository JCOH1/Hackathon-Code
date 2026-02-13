FinanceQuest - Desktop Financial Simulation Game
A comprehensive financial simulation game built with Python and Pygame that teaches personal finance, investment, and life planning through realistic decision-based gameplay. Now with data science features including a post‑game dashboard and machine learning goal prediction!

Features
3-Year Simulation: Navigate 36 months of financial decisions

Character Customization: Choose your social class, education level, and difficulty

Complete Financial System: Manage income, expenses, debt, investments, and emergency funds

Well-Being Engine: Track happiness and stress levels that affect gameplay

Debuff System: Face consequences like addiction, distraction, and burnout

Life Choices: Make decisions about leisure, high-risk activities, and personal growth

Random Events: Deal with emergencies like medical issues, job loss, and market crashes

Goals & Scoring: Complete objectives and compete for high scores

Tutorial System: Learn the mechanics through an interactive tutorial

🤖 AI-Powered Financial Assistant: Chat with "Finley the Financial Fox" for personalized advice, game tips, and financial education using LangChain and Azure OpenAI

🆕 Data Science Features
1. Post‑Game Dashboard
After finishing a game, click "View Statistics" to see a beautifully styled dashboard with:

Net worth progression over time

Happiness vs. stress trends

Final asset composition (cash, investments, emergency fund, debt)

Action statistics (total invested, saved, debt paid, leisure/risky actions)

The dashboard uses pandas for data handling and matplotlib for plotting, all embedded directly into the pygame window.

2. Goal Completion Prediction (Machine Learning)
A scikit‑learn model predicts your likelihood of completing each of the four goals based on your first 6 months of gameplay. After month 6, click the "PREDICT GOALS" button to see:

Probability of achieving Net Worth $50k

Probability of achieving Emergency Fund $10k

Probability of becoming Debt‑Free

Probability of reaching 70+ Happiness

The model learns from your own play history – the more you play, the smarter it becomes!

Installation
Prerequisites
Python 3.7 or higher

pip (Python package installer)

Steps
Install Python (if not already installed)

Download from python.org

Make sure to check "Add Python to PATH" during installation

Install required packages

bash
pip install pygame pandas matplotlib scikit-learn joblib python-dotenv langchain langchain-openai langchain-community
Or use the provided requirements.txt:

bash
pip install -r requirements.txt
(Optional) Set up Azure OpenAI for advanced chatbot

Create a .env file with your Azure OpenAI credentials:

text
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_DEPLOYMENT=your_deployment_name

Running the Game
Windows
bash
python inject_wins.py
python train_goal_model.py
python rijika.py

macOS/Linux
bash
python3 inject_wins.py
python3 train_goal_model.py
python3 rijika.py
How to Play
Game Setup
Choose Your Social Class:

Upper Class: High income, no debt

Middle Class: Moderate income, some debt

Lower Class: Limited resources, significant debt

Choose Your Education:

Polytechnic: Standard education (no additional cost)

University: Higher income but significant debt

Master's Degree: Maximum earning potential with substantial investment

Choose Difficulty:

Easy: Fewer emergencies, stable markets

Normal: Balanced challenge

Hard: Frequent emergencies, volatile markets

Gameplay
Each turn represents one month. You can:

Financial Management:

Invest money in the stock market

Withdraw investments when needed

Build your emergency fund

Pay off debt

Leisure Activities:

Take vacations, go to theme parks, fine dining, staycations

Increases happiness, reduces stress

High-Risk Activities (be careful!):

Shopping, gambling, clubbing, smoking

Can lead to addiction debuffs

Growth & Utility:

Buy a vehicle

Invest in relationships

Further Education:

Upgrade to University Degree during gameplay (+$1500/month income, $30,000 debt, +15 stress)

Upgrade to Master's Degree (requires university first, +$1000/month additional, $50,000 debt, +20 stress)

Treatment (when needed):

Treat addiction ($1500)

Seek therapy for stress/unhappiness ($800)

Goals
Complete these goals for bonus points:

Achieve $50,000 Net Worth

Build $10,000 Emergency Fund

Become Debt-Free

Maintain 70+ Happiness

Win Conditions
Survive all 36 months

Complete as many goals as possible

Maximize your final score

Lose Conditions
Go more than $10,000 into debt

Burnout (100% stress or <10% happiness) multiple times

📊 Data Science Features – In Detail
Dashboard
Accessed via "View Statistics" on the game over screen.

All charts use the game’s dark theme with neon accents.

Click the red ✕ or press ESC to close.

Goal Prediction
Collect Data: Play several games (each at least 6 months). Data is automatically saved in goal_training_data.json.

Train the Model: Run the training script (provided separately) to create the model files:

bash
python train_goal_model.py
(This script is not included in the main game; you can create it as described below.)

Use in Game: Once goal_predictor.pkl and goal_features.pkl exist, the "PREDICT GOALS" button appears. Click it after month 6 to see your goal completion probabilities.

Training Script Example
Create a file train_goal_model.py in the same folder:

python
import json
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier

with open('goal_training_data.json') as f:
    data = json.load(f)
df = pd.DataFrame(data)

features = ['early_avg_happiness','early_avg_stress','early_total_investments',
            'early_total_saved','early_total_debt_paid','early_num_leisure','early_num_risky']
X = df[features]
y = df[['goal_networth','goal_emergency','goal_debtfree','goal_happiness']]

model = MultiOutputClassifier(RandomForestClassifier(n_estimators=100))
model.fit(X, y)

joblib.dump(model, 'goal_predictor.pkl')
joblib.dump(features, 'goal_features.pkl')
print("Model saved!")
Controls
Mouse: Click buttons to make choices

Mouse Wheel: Scroll through actions (in gameplay screen)

ESC: Close dashboard or modals

Scoring System
Your final score is calculated based on:

Net Worth (Money + Investments + Emergency Fund - Debt)

Goals Completed (5,000 points each)

Final Happiness (×100)

Months Survived (×500)

Tips
Balance is Key: Don't neglect your happiness while building wealth

Emergency Fund: Build this early to handle unexpected events

Debt Management: High debt increases stress and costs you money in interest

Watch Your Debuffs: Addiction and distraction can severely impact your income

Invest Wisely: Markets are volatile, especially on higher difficulties

Don't Burn Out: If stress hits 100% or happiness drops below 10%, you'll be forced into medical leave

Use the Dashboard: Review your performance after each game to identify areas for improvement

Train the Model: The more games you play, the smarter the goal predictor becomes – retrain occasionally!

Troubleshooting
"pygame not found" error
bash
pip install pygame
Missing scikit-learn / pandas / matplotlib
bash
pip install scikit-learn pandas matplotlib joblib
Game runs slowly
Close other applications

The game runs at 60 FPS by default

Dashboard doesn't appear
Make sure you have played at least one full game (reached month 24 or lost)

Check that matplotlib is installed correctly

Prediction button shows "Need at least 6 months..."
Keep playing! The prediction only works after month 6.

"No trained goal predictor found"
You need to run the training script after collecting enough data.

System Requirements
OS: Windows 10+, macOS 10.13+, or Linux

RAM: 512 MB minimum

Display: 1400x900 minimum resolution recommended

Python: 3.7 or higher

Disk Space: ~100 MB for dependencies

File Structure
text
financequest/
├── rijika.py                # Main game file
├── train_goal_model.py      # (optional) Training script for ML model
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── .env                     # (optional) Azure OpenAI credentials
├── highscore.json           # Created automatically
├── game_summaries.json      # Saved game summaries
├── goal_training_data.json  # Data for ML model (grows with each game)
├── inject_wins.py           # Generates synthetic winning data for the ML model

Credits
Created as an educational tool to teach financial literacy through gamification.
AI features powered by LangChain and Azure OpenAI.
Data visualisation with matplotlib and pandas.
Machine learning with scikit-learn.

License
This game is provided for educational purposes.

Enjoy playing FinanceQuest and mastering your financial future! 🎮💰📊🤖
