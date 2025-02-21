from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, date
from smart_scheduler import SmartScheduler
import pandas as pd
from flask import session, flash, g
from functools import wraps
from models import User
 # Change this to a secure secret key

app = Flask(__name__)
scheduler = SmartScheduler()

# Initialize User model
user_model = User()

app.secret_key = 'lidi' 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = user_model.get_user_by_id(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_id = user_model.verify_user(username, password)
        if user_id:
            session['user_id'] = user_id
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if user_model.create_user(username, password, email):
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        flash('Username or email already exists', 'error')
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Load and train the model with our dataset
try:
    training_data = pd.read_csv('training_data.csv')
    scheduler.train_model(training_data)
except Exception as e:
    print(f"Warning: Could not load training data: {e}")
    # Generate some sample data if training data is not available
    training_data = scheduler.generate_sample_data()
    scheduler.train_model(training_data)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        try:
            task_data = {
                'user_id': session['user_id'],  # Add user_id
                'course': request.form.get('course'),
                'task_type': request.form.get('task_type'),
                'difficulty': int(request.form.get('difficulty')),
                'total_available_time': float(request.form.get('total_available_time')),
                'deadline_days': int(request.form.get('deadline_days')),
                'due_date': request.form.get('due_date'),
                'due_time': request.form.get('due_time', '23:59')
            }
            
            task_id, predicted_time = scheduler.add_task(**task_data)
            
            return jsonify({
                'task_id': task_id,
                'predicted_time': round(predicted_time, 2)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return render_template('add_task.html', today=date.today().isoformat())

@app.route('/update_task/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    try:
        # First verify that the task belongs to the current user
        conn = scheduler.connect_db()
        c = conn.cursor()
        c.execute('SELECT user_id FROM tasks WHERE id = ?', (task_id,))
        task = c.fetchone()
        conn.close()

        if not task or task[0] != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403

        actual_time = float(request.form['actual_time'])
        scheduler.update_actual_time(task_id, actual_time)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        return redirect(url_for('schedule'))
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
        return f"Error updating task: {str(e)}", 400

@app.route('/update_status/<int:task_id>', methods=['POST'])
@login_required
def update_status(task_id):
    try:
        # First verify that the task belongs to the current user
        conn = scheduler.connect_db()
        c = conn.cursor()
        c.execute('SELECT user_id FROM tasks WHERE id = ?', (task_id,))
        task = c.fetchone()
        conn.close()

        if not task or task[0] != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403

        status = request.form['status']
        scheduler.update_task_status(task_id, status)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        return redirect(url_for('schedule'))
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
        return f"Error updating task status: {str(e)}", 400

@app.route('/schedule')
@login_required
def schedule():
    try:
        conn = scheduler.connect_db()
        
        # Get current timestamp in local timezone
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Updated query with explicit datetime comparison
        tasks_df = pd.read_sql_query(f'''
            WITH task_status AS (
                SELECT *,
                    CASE 
                        WHEN status = 'completed' THEN 'completed'
                        WHEN datetime(due_date || ' ' || due_time) < datetime(?) THEN 'overdue'
                        ELSE 'pending'
                    END as current_status,
                    CASE
                        WHEN datetime(due_date || ' ' || due_time) < datetime(?)
                        THEN ROUND((julianday(?) - julianday(due_date || ' ' || due_time)) * 24, 1)
                        ELSE 0
                    END as hours_overdue
                FROM tasks
                WHERE user_id = ?
            )
            SELECT * FROM task_status
            ORDER BY 
                CASE current_status
                    WHEN 'completed' THEN 3
                    WHEN 'pending' THEN 1
                    ELSE 2  -- overdue tasks
                END,
                datetime(due_date || ' ' || due_time) ASC
        ''', conn, params=(current_time, current_time, current_time, session['user_id']))
        
        # Process the hours overdue into a more readable format
        def format_overdue_time(hours):
            if hours == 0:
                return None
            if hours < 24:
                return f"{int(hours)} hour{'s' if hours != 1 else ''}"
            days = int(hours // 24)
            remaining_hours = int(hours % 24)
            if remaining_hours == 0:
                return f"{days} day{'s' if days != 1 else ''}"
            return f"{days} day{'s' if days != 1 else ''} and {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"

        # Add formatted overdue time to each task
        tasks = tasks_df.replace({float('nan'): None, pd.NaT: None}).to_dict('records')
        for task in tasks:
            if task['current_status'] == 'overdue':
                task['overdue_time'] = format_overdue_time(task['hours_overdue'])
                print(f"Task {task['course']} is overdue by {task['overdue_time']}")  # Debug print
        
        # Debug print
        print(f"Total tasks: {len(tasks)}")
        for task in tasks:
            print(f"Task: {task['course']}, Status: {task['current_status']}, Due: {task['due_date']} {task['due_time']}")
        
        return render_template('schedule.html', tasks=tasks)
    except Exception as e:
        print("Error in schedule:", str(e))  # For debugging
        return f"Error loading schedule: {str(e)}", 500

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = scheduler.connect_db()
        tasks_df = pd.read_sql_query('''
            SELECT *, 
                   CASE 
                       WHEN status = 'completed' THEN 'completed'
                       WHEN datetime(due_date || ' ' || due_time) < datetime('now', 'localtime') THEN 'overdue'
                       ELSE 'pending'
                   END as current_status
            FROM tasks 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', conn, params=(session['user_id'],))
        
        tasks = tasks_df.replace({float('nan'): None}).to_dict('records')
        insights = scheduler.get_user_insights(session['user_id'])
        
        # Prepare analytics data for completed tasks
        completed_tasks = tasks_df[tasks_df['actual_time'].notna()]
        
        analytics_data = {
            'accuracy': {
                'labels': completed_tasks['course'].tolist(),
                'predicted': completed_tasks['predicted_time'].tolist(),
                'actual': completed_tasks['actual_time'].tolist()
            },
            'utilization': {
                'used': float(completed_tasks['actual_time'].sum() or 0),
                'available': float(completed_tasks['total_available_time'].sum() or 0)
            },
            'taskType': {
                'labels': completed_tasks.groupby('task_type')['actual_time'].mean().index.tolist(),
                'data': completed_tasks.groupby('task_type')['actual_time'].mean().tolist()
            },
            'difficulty': {
                'data': [
                    {'x': int(row['difficulty']), 'y': float(row['actual_time'])} 
                    for _, row in completed_tasks.iterrows()
                ]
            }
        }
        
        return render_template('dashboard.html', 
                             tasks=tasks, 
                             insights=insights,
                             analytics_data=analytics_data)
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 