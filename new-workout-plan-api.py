# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from enum import Enum

app = FastAPI()

class MuscleGroup(str, Enum):
    CHEST = "Chest"
    BACK = "Back"
    SHOULDERS = "Shoulders"
    BICEPS = "Biceps"
    TRICEPS = "Triceps"
    LEGS = "Legs"
    CORE = "Core"

class Exercise(BaseModel):
    id: str
    name: str
    muscle_groups: List[MuscleGroup]
    description: str
    equipment_needed: Optional[str]
    difficulty_level: str
    recommended_rest: int  # in seconds

class ExerciseSelection(BaseModel):
    exercise_id: str
    sets: int
    reps: int
    rest_time: int  # in seconds

class WorkoutSession(BaseModel):
    date: str
    exercises: List[ExerciseSelection]

class WorkoutCompletion(BaseModel):
    exercise_id: str
    completed_sets: int
    actual_reps: List[int]
    time_taken: int  # in seconds
    difficulty_rating: int  # 1-5

class WorkoutHistory(BaseModel):
    session_id: str
    date: str
    exercises_completed: List[WorkoutCompletion]
    total_time: int
    overall_difficulty: float

# Exercise Database
EXERCISE_DATABASE = {
    "push-up-001": {
        "id": "push-up-001",
        "name": "Push-ups",
        "muscle_groups": [MuscleGroup.CHEST, MuscleGroup.SHOULDERS, MuscleGroup.TRICEPS],
        "description": "Standard push-up position, lower body until chest nearly touches ground",
        "equipment_needed": None,
        "difficulty_level": "beginner",
        "recommended_rest": 60
    },
    "squat-001": {
        "id": "squat-001",
        "name": "Bodyweight Squats",
        "muscle_groups": [MuscleGroup.LEGS],
        "description": "Stand with feet shoulder-width apart, lower body until thighs are parallel to ground",
        "equipment_needed": None,
        "difficulty_level": "beginner",
        "recommended_rest": 60
    },
    # Add more exercises here...
}

# In-memory storage (replace with database in production)
workout_history = {}

@app.get("/exercises")
async def get_exercises():
    return list(EXERCISE_DATABASE.values())

@app.get("/exercises/{muscle_group}")
async def get_exercises_by_muscle(muscle_group: MuscleGroup):
    return [
        exercise for exercise in EXERCISE_DATABASE.values()
        if muscle_group in exercise["muscle_groups"]
    ]

@app.post("/validate-workout")
async def validate_workout(selections: List[ExerciseSelection]):
    """Validate exercise selections and provide suggestions"""
    muscle_group_count = {}
    warnings = []
    
    for selection in selections:
        exercise = EXERCISE_DATABASE.get(selection.exercise_id)
        if not exercise:
            raise HTTPException(status_code=400, detail=f"Exercise {selection.exercise_id} not found")
            
        # Count muscle group usage
        for muscle in exercise["muscle_groups"]:
            muscle_group_count[muscle] = muscle_group_count.get(muscle, 0) + 1
            
            # Warn if same muscle group used too much
            if muscle_group_count[muscle] > 2:
                warnings.append(f"Warning: {muscle.value} is being trained {muscle_group_count[muscle]} times. "
                              f"This might lead to excessive fatigue. Consider spreading exercises across different muscle groups.")
    
    return {
        "is_valid": len(warnings) == 0,
        "warnings": warnings,
        "muscle_group_distribution": muscle_group_count
    }

@app.post("/start-workout")
async def start_workout(workout: WorkoutSession):
    session_id = f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Validate exercises
    for exercise_selection in workout.exercises:
        if exercise_selection.exercise_id not in EXERCISE_DATABASE:
            raise HTTPException(status_code=400, detail=f"Exercise {exercise_selection.exercise_id} not found")
    
    return {
        "session_id": session_id,
        "started_at": datetime.now().isoformat(),
        "exercise_plan": [
            {
                **EXERCISE_DATABASE[ex.exercise_id],
                "planned_sets": ex.sets,
                "planned_reps": ex.reps,
                "rest_time": ex.rest_time
            }
            for ex in workout.exercises
        ]
    }

@app.post("/complete-workout/{session_id}")
async def complete_workout(session_id: str, completion: List[WorkoutCompletion]):
    if not completion:
        raise HTTPException(status_code=400, detail="No exercises completed")
    
    total_time = sum(ex.time_taken for ex in completion)
    overall_difficulty = sum(ex.difficulty_rating for ex in completion) / len(completion)
    
    history_entry = WorkoutHistory(
        session_id=session_id,
        date=datetime.now().isoformat(),
        exercises_completed=completion,
        total_time=total_time,
        overall_difficulty=overall_difficulty
    )
    
    workout_history[session_id] = history_entry.dict()
    
    return history_entry

@app.get("/workout-history/{date}")
async def get_workout_history(date: str):
    # Filter history for given date
    daily_history = [
        session for session in workout_history.values()
        if session["date"].startswith(date)
    ]
    
    if not daily_history:
        return {"message": "No workouts found for this date"}
    
    return daily_history

@app.get("/export-history/{date}")
async def export_workout_history(date: str):
    daily_history = await get_workout_history(date)
    
    if "message" in daily_history:
        return daily_history
    
    # Convert to exportable format
    export_data = {
        "date": date,
        "total_sessions": len(daily_history),
        "sessions": daily_history
    }
    
    return export_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
