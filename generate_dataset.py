import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Create a list of sample data
data = []

# Define possible values
courses = ['Mathematics', 'Physics', 'Computer Science', 'History', 'Literature', 
          'Chemistry', 'Biology', 'Economics']
task_types = ['Assignment', 'Project', 'Exam Preparation', 'Quiz', 'Lab Report']

# Generate 30 realistic entries
for _ in range(30):
    course = np.random.choice(courses)
    task_type = np.random.choice(task_types)
    difficulty = np.random.randint(1, 6)  # 1-5 scale
    total_available_time = round(np.random.uniform(2, 12), 1)  # 2-12 hours
    deadline_days = np.random.randint(1, 15)  # 1-14 days
    
    # Calculate actual_time based on realistic factors with some randomness
    base_time = difficulty * 1.2  # Base time increases with difficulty
    deadline_factor = max(0.8, 1 - (deadline_days / 20))  # Urgent tasks take more time
    available_time_factor = min(1.2, total_available_time / 8)  # More available time might mean more thorough work
    
    # Add some task type specific modifications
    type_factors = {
        'Assignment': 1.0,
        'Project': 1.4,
        'Exam Preparation': 1.3,
        'Quiz': 0.7,
        'Lab Report': 1.2
    }
    
    # Calculate actual time with some random variation
    actual_time = round(base_time * deadline_factor * available_time_factor * 
                       type_factors[task_type] * np.random.uniform(0.8, 1.2), 1)
    
    # Ensure actual_time is reasonable
    actual_time = min(actual_time, total_available_time * 0.9)  # Can't take more than available time
    actual_time = max(actual_time, 0.5)  # Minimum 30 minutes
    
    data.append({
        'course': course,
        'task_type': task_type,
        'difficulty': difficulty,
        'total_available_time': total_available_time,
        'deadline_days': deadline_days,
        'actual_time': actual_time
    })

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv('training_data.csv', index=False)

# Display the first few rows
print("First few rows of the generated dataset:")
print(df.head())

# Display summary statistics
print("\nDataset summary:")
print(df.describe())

# Display value counts for categorical variables
print("\nCourse distribution:")
print(df['course'].value_counts())
print("\nTask type distribution:")
print(df['task_type'].value_counts())