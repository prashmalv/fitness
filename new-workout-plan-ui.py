# streamlit_app.py
import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import json
import time
import base64
from io import BytesIO

# Initialize session state
if 'current_exercise' not in st.session_state:
    st.session_state.current_exercise = 0
if 'workout_in_progress' not in st.session_state:
    st.session_state.workout_in_progress = False
if 'completed_exercises' not in st.session_state:
    st.session_state.completed_exercises = []
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'session_id' not in st.session_state:
    st.session_state.session_id = None

def get_exercises():
    response = requests.get("http://localhost:8000/exercises")
    if response.status_code == 200:
        return response.json()
    return []

def validate_workout(selections):
    response = requests.post(
        "http://localhost:8000/validate-workout",
        json=selections
    )
    return response.json() if response.status_code == 200 else None

def start_timer(duration):
    start_time = time.time()
    placeholder = st.empty()
    
    while time.time() - start_time < duration and st.session_state.timer_running:
        remaining = duration - int(time.time() - start_time)
        mins, secs = divmod(remaining, 60)
        placeholder.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
        time.sleep(1)
    
    placeholder.empty()
    return time.time() - start_time

def download_history(export_data):
    df = pd.json_normalize(export_data['sessions'])
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="workout_history.csv">Download Workout History</a>'
    return href

def main():
    st.title("🏋️‍♂️ Custom Workout Tracker")
    
    # Sidebar for exercise selection
    st.sidebar.header("Exercise Selection")
    
    exercises = get_exercises()
    
    if not st.session_state.workout_in_progress:
        # Exercise selection form
        with st.form("exercise_selection"):
            selected_exercises = []
            
            for exercise in exercises:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    if st.checkbox(f"{exercise['name']} ({', '.join(exercise['muscle_groups'])})", key=exercise['id']):
                        with col2:
                            sets = st.number_input(f"Sets for {exercise['name']}", 1, 10, 3, key=f"sets_{exercise['id']}")
                        with col3:
                            reps = st.number_input(f"Reps for {exercise['name']}", 1, 50, 10, key=f"reps_{exercise['id']}")
                        
                        selected_exercises.append({
                            "exercise_id": exercise['id'],
                            "sets": sets,
                            "reps": reps,
                            "rest_time": exercise['recommended_rest']
                        })
            
            if st.form_submit_button("Validate & Start Workout"):
                if selected_exercises:
                    # Validate workout
                    validation = validate_workout(selected_exercises)
                    
                    if validation["warnings"]:
                        st.warning("\n".join(validation["warnings"]))
                        st.write("Muscle Group Distribution:")
                        st.json(validation["muscle_group_distribution"])
                    
                    # Start workout
                    response = requests.post(
                        "http://localhost:8000/start-workout",
                        json={
                            "date": datetime.now().isoformat(),
                            "exercises": selected_exercises
                        }
                    )
                    
                    if response.status_code == 200:
                        workout_data = response.json()
                        st.session_state.session_id = workout_data["session_id"]
                        st.session_state.workout_plan = workout_data["exercise_plan"]
                        st.session_state.workout_in_progress = True
                        st.session_state.current_exercise = 0
                        st.experimental_rerun()
                else:
                    st.error("Please select at least one exercise")
    
    else:
        # Workout in progress
        current_exercise = st.session_state.workout_plan[st.session_state.current_exercise]
        
        st.header(f"Current Exercise: {current_exercise['name']}")
        st.subheader(f"Set {len(st.session_state.completed_exercises) + 1} of {current_exercise['planned_sets']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"Target Reps: {current_exercise['planned_reps']}")
            st.write(f"Rest Time: {current_exercise['rest_time']} seconds")
        
        with col2:
            st.write("Instructions:")
            st.write(current_exercise['description'])
        
        # Timer controls
        if not st.session_state.timer_running:
            if st.button("Start Set"):
                st.session_state.timer_running = True
                actual_reps = st.number_input("How many reps did you complete?", 0, 100, current_exercise['planned_reps'])
                difficulty = st.slider("How difficult was this set? (1-5)", 1, 5, 3)
                
                time_taken = start_timer(current_exercise['rest_time'])
                
                st.session_state.completed_exercises.append({
                    "exercise_id": current_exercise['id'],
                    "completed_sets": len(st.session_state.completed_exercises) + 1,
                    "actual_reps": [actual_reps],
                    "time_taken": int(time_taken),
                    "difficulty_rating": difficulty
                })
                
                st.session_state.timer_running = False
                
                # Check if exercise is complete
                if len(st.session_state.completed_exercises) >= current_exercise['planned_sets']:
                    st.session_state.current_exercise += 1
                    if st.session_state.current_exercise >= len(st.session_state.workout_plan):
                        # Workout complete
                        response = requests.post(
                            f"http://localhost:8000/complete-workout/{st.session_state.session_id}",
                            json=st.session_state.completed_exercises
                        )
                        
                        if response.status_code == 200:
                            st.success("Workout Complete!")
                            st.session_state.workout_in_progress = False
                            st.session_state.completed_exercises = []
                            st.experimental_rerun()
                    else:
                        st.experimental_rerun()
        
        # Show progress
        progress = len(st.session_state.completed_exercises) / (current_exercise['planned_sets'] * len(st.session_state.workout_plan))
        st.progress(progress)
    
    # History section
    st.header("Workout History")
    selected_date = st.date_input("Select Date", datetime.now())
    
    if st.button("View History"):
        response = requests.get(f"http://localhost:8000/workout-history/{selected_date.isoformat()}")
        if response.status_code == 200:
            history = response.json()
            if "message" not in history:
                for session in history:
                    st.subheader(f"Session: {session['session_id']}")
                    st.write(f"Total Time: {session['total_time']} seconds")
                    st.write(f"Overall Difficulty: {session['overall_difficulty']:.1f}/5")
                    
                    # Create exercise completion table
                    exercises_df = pd.DataFrame(session['exercises_completed'])
                    st.dataframe(exercises_df)
                
                # Export button
                export_response = requests.get(f"http://localhost:8000/export-history/{selected_date.isoformat()}")
                if export_response.status_code == 200:
                    st.markdown(download_history(export_response.json()), unsafe_allow_html=True)
            else:
                st.info(history["message"])

if __name__ == "__main__":
    main()
