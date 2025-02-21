from smart_scheduler import SmartScheduler
import pandas as pd

def main():
    # Initialize the scheduler
    scheduler = SmartScheduler()
    
    # Load the real training data
    print("Loading training data...")
    training_data = pd.read_csv('training_data.csv')
    
    # Train the model with real data
    print("Training model...")
    scheduler.train_model(training_data)
    
    # Add a test task
    print("\nAdding a test task...")
    task_id, predicted_time = scheduler.add_task(
        course="Computer Science",
        task_type="Assignment",
        difficulty=3,
        total_available_time=5,
        deadline_days=7
    )
    
    print(f"Task ID: {task_id}")
    print(f"Predicted time needed: {predicted_time:.2f} hours")
    
    # Simulate completing the task
    print("\nUpdating with actual completion time...")
    scheduler.update_actual_time(task_id, 4.5)
    
    # Get insights
    print("\nGetting insights...")
    insights = scheduler.get_user_insights()
    print(insights)

if __name__ == "__main__":
    main()