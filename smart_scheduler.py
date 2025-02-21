import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
import sqlite3
from datetime import datetime, timedelta

class SmartScheduler:
    def __init__(self, db_path='scheduler.db'):
        self.db_path = db_path
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(random_state=42)
        self.setup_database()
    
    def connect_db(self):
        """Create a database connection"""
        return sqlite3.connect(self.db_path)
    
    def setup_database(self):
        """Initialize SQLite database with required tables"""
        conn = self.connect_db()
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course TEXT NOT NULL,
                task_type TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                total_available_time REAL NOT NULL,
                deadline_days INTEGER NOT NULL,
                predicted_time REAL,
                actual_time REAL,
                due_date DATE NOT NULL,
                due_time TIME NOT NULL DEFAULT '23:59',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def preprocess_data(self, df):
        """Preprocess data for model training"""
        # Create copies to avoid modifying original data
        X = df.copy()
        y = X.pop('actual_time') if 'actual_time' in X else None
        
        # Encode categorical variables
        categorical_cols = ['course', 'task_type']
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            
            # Get unique values including new ones
            unique_values = list(self.label_encoders[col].classes_) if hasattr(self.label_encoders[col], 'classes_') else []
            current_values = X[col].unique()
            all_values = list(set(unique_values + list(current_values)))
            
            # Fit with all values and transform
            self.label_encoders[col].fit(all_values)
            X[col] = self.label_encoders[col].transform(X[col])
        
        # Scale numerical features
        numerical_cols = ['difficulty', 'total_available_time', 'deadline_days']
        if y is not None:  # Only fit during training
            self.scaler.fit(X[numerical_cols])
        X[numerical_cols] = self.scaler.transform(X[numerical_cols])
        
        return X, y
    
    def train_model(self, df):
        """Train the ML model"""
        X, y = self.preprocess_data(df)
        self.model.fit(X, y)
    
    def predict_time(self, course, task_type, difficulty, total_available_time, deadline_days):
        """Predict time needed for a task"""
        data = pd.DataFrame({
            'course': [course],
            'task_type': [task_type],
            'difficulty': [difficulty],
            'total_available_time': [total_available_time],
            'deadline_days': [deadline_days]
        })
        
        X, _ = self.preprocess_data(data)
        predicted_time = self.model.predict(X)[0]
        return max(0.5, predicted_time)
    
    def add_task(self, user_id, course, task_type, difficulty, total_available_time, deadline_days, due_date, due_time):
        """Add a new task with user_id"""
        predicted_time = self.predict_time(
            course, task_type, difficulty, total_available_time, deadline_days
        )
        
        conn = self.connect_db()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO tasks (
                user_id, course, task_type, difficulty, total_available_time, 
                deadline_days, predicted_time, due_date, due_time, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, course, task_type, difficulty, total_available_time, 
            deadline_days, predicted_time, due_date, due_time, 'pending'))
        
        task_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return task_id, predicted_time
    
    def update_task_status(self, task_id, status):
        """Update task status (pending/completed/overdue)"""
        conn = self.connect_db()
        c = conn.cursor()
        
        c.execute('''
            UPDATE tasks 
            SET status = ? 
            WHERE id = ?
        ''', (status, task_id))
        
        conn.commit()
        conn.close()
    
    def get_schedule(self, user_id):
        """Get tasks ordered by due date with status for specific user"""
        conn = self.connect_db()
        df = pd.read_sql_query('''
            SELECT *, 
                CASE 
                    WHEN status = 'completed' THEN 'completed'
                    WHEN datetime(due_date || ' ' || due_time) < datetime('now', 'localtime') THEN 'overdue'
                    ELSE 'pending'
                END as current_status,
                CASE
                    WHEN datetime(due_date || ' ' || due_time) < datetime('now', 'localtime')
                    THEN ROUND((julianday('now', 'localtime') - julianday(due_date || ' ' || due_time)) * 24, 1)
                    ELSE 0
                END as hours_overdue
            FROM tasks 
            WHERE user_id = ?
            ORDER BY 
                CASE status
                    WHEN 'completed' THEN 3
                    WHEN 'pending' THEN 1
                    ELSE 2  -- overdue tasks
                END,
                datetime(due_date || ' ' || due_time) ASC
        ''', conn, params=(user_id,))
        conn.close()
        
        return df
    
    def update_actual_time(self, task_id, actual_time):
        """Update task with actual completion time"""
        conn = self.connect_db()
        c = conn.cursor()
        
        c.execute('''
            UPDATE tasks 
            SET actual_time = ? 
            WHERE id = ?
        ''', (actual_time, task_id))
        
        conn.commit()
        conn.close()
    
    def get_user_insights(self, user_id):
        """Generate insights based on user's task history"""
        conn = self.connect_db()
        df = pd.read_sql_query('''
            SELECT * FROM tasks 
            WHERE user_id = ? AND actual_time IS NOT NULL
        ''', conn, params=(user_id,))
        conn.close()
        
        if len(df) == 0:
            return "No completed tasks yet. Update some tasks with actual completion times to see insights!"
        
        insights = []
        
        # Basic completion stats
        completed_tasks = len(df)
        insights.append(f"You have completed {completed_tasks} task{'s' if completed_tasks != 1 else ''}.")
        
        # Prediction accuracy
        df['prediction_error'] = abs(df['predicted_time'] - df['actual_time'])
        avg_error = df['prediction_error'].mean()
        insights.append(f"Average prediction error: {avg_error:.2f} hours")
        
        # Time usage patterns
        df['time_ratio'] = df['actual_time'] / df['total_available_time'] * 100
        avg_time_ratio = df['time_ratio'].mean()
        insights.append(f"On average, you use {avg_time_ratio:.1f}% of your available time")
        
        # Course-specific insights (if there are at least 2 courses)
        if len(df['course'].unique()) >= 2:
            course_errors = df.groupby('course')['prediction_error'].mean()
            best_course = course_errors.idxmin()
            worst_course = course_errors.idxmax()
            insights.append(f"Most accurate predictions are for: {best_course}")
            insights.append(f"Less accurate predictions are for: {worst_course}")
        
        # Task type patterns (if there are at least 2 task types)
        if len(df['task_type'].unique()) >= 2:
            task_durations = df.groupby('task_type')['actual_time'].mean()
            longest_task = task_durations.idxmax()
            shortest_task = task_durations.idxmin()
            insights.append(f"On average, {longest_task}s take the longest ({task_durations[longest_task]:.1f} hours)")
            insights.append(f"while {shortest_task}s take the shortest ({task_durations[shortest_task]:.1f} hours)")
        
        # Time management tips based on patterns
        if avg_time_ratio > 90:
            insights.append("Tip: You're using most of your available time. Consider allocating more buffer time.")
        elif avg_time_ratio < 50:
            insights.append("Tip: You're finishing tasks quickly. You might be able to take on more work.")
        
        # Recent trends (if there are at least 3 tasks)
        if len(df) >= 3:
            recent_tasks = df.sort_values('created_at').tail(3)
            recent_accuracy = recent_tasks['prediction_error'].mean()
            if recent_accuracy < avg_error:
                insights.append("Good news! Your recent tasks are more accurately predicted than earlier ones.")
        
        return "\n".join(insights)