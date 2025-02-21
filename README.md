# Smart Scheduler - AI-Powered Task Management System


# Overview


Smart Scheduler is an intelligent task management system designed for students, leveraging machine learning to predict task completion times and optimize study schedules. The system uses a Random Forest Regressor to learn from user patterns and provide personalized time predictions.
# 🚀  Features

AI-powered time predictions
Personalized task management
Real-time analytics dashboard
User authentication system
Interactive schedule visualization
Progress tracking
Task difficulty analysis

# 📋 Prerequisites

Python 3.11 or higher
Flask
SQLite
scikit-learn
pandas
numpy
Chart.js

🔧 Installation
bashCopy# Clone the repository
git clone https://github.com/lidiayon/smart-scheduler.git

# Navigate to project directory
cd smart-scheduler

# Create virtual environment
python -m venv venv

# Activate virtual environment
# For Windows
venv\Scripts\activate
# For macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
📁 Project Structure
Copysmart_scheduler/
├── app.py                 # Main Flask application
├── smart_scheduler.py     # ML model and core logic
├── models.py             # Database models
├── generate_dataset.py   # Training data generation
├── test_scheduler.py     # Testing suite
├── scheduler.db         # SQLite database
├── training_data.csv    # ML training data
└── templates/          # HTML templates
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── base.html
    ├── dashboard.html
    ├── index.html
    ├── landing.html
    ├── add_task.html
    └── schedule.html
# 🤖 Machine Learning Component
The system uses a Random Forest Regressor model that considers:

Course type
Task type
Difficulty level (1-5)
Available study time
Deadline proximity

📊 Analytics
Four main analytics components:

Prediction Accuracy

Compares predicted vs actual times
Shows model performance


Time Utilization

Visualizes time usage efficiency
Shows available vs used time


Time by Task Type

Breaks down time spent by task category
Helps in understanding workload


Difficulty vs Time

Shows correlation between task difficulty and duration
Helps in effort estimation



🔐 Authentication

User registration system
Secure login functionality
Session management
User-specific data isolation

💻 Usage

Register a new account
Log in to your dashboard
Add tasks with details:

Course name
Task type
Difficulty level
Due date
Available time


Get AI-powered time predictions
Track task completion
View analytics and insights

🌐 API Endpoints
pythonCopy/           # Landing page
/login      # User login
/register   # User registration
/dashboard  # Main dashboard
/add_task   # Task creation
/schedule   # Schedule view
📈 Database Schema
sqlCopyCREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    email TEXT UNIQUE
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    course TEXT,
    task_type TEXT,
    difficulty INTEGER,
    total_available_time REAL,
    deadline_days INTEGER,
    predicted_time REAL,
    actual_time REAL,
    due_date DATE,
    status TEXT,
    created_at TIMESTAMP
);
🔄 Development Process

Initial Setup (Week 1)

Project planning
Requirements gathering
Initial design


Core Development (Week 2)

Database implementation
ML model development
Basic functionality


Frontend Development (Week 3)

User interface
Authentication system
Task management


Analytics Implementation (Week 4)

Data visualization
Performance metrics
Testing


Final Phase (Week 5)

Documentation
Final testing
Deployment



🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
👥 Authors

Ssewit (@sewit1311)
Lidia (@lidiayon)

🙏 Acknowledgments

Flask Documentation
scikit-learn Documentation
Chart.js Documentation
Tailwind CSS

📧 Contact
For any queries, please reach out to: sewit1311@gmail.com
🐛 Bug Reporting
Please report bugs in the Issues section.
