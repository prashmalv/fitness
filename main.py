# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import random

app = FastAPI()

class WorkoutPlanRequest(BaseModel):
    fitness_level: str  # beginner, intermediate, advanced
    duration_minutes: int  # 30 or 60
    start_date: str  # YYYY-MM-DD

class Exercise(BaseModel):
    name: str
    sets: int
    reps: str
    rest_seconds: int

class WorkoutDay(BaseModel):
    day: str
    focus_area: str
    exercises: List[Exercise]
    calories_burn_estimate: int

class Meal(BaseModel):
    name: str
    calories: int
    protein: int
    carbs: int
    fats: int
    description: str

class DietDay(BaseModel):
    day: str
    total_calories: int
    meals: List[Meal]

class WeeklyPlan(BaseModel):
    workout_plan: List[WorkoutDay]
    diet_plan: List[DietDay]

# Exercise database
EXERCISE_LIBRARY = {
    "beginner": {
        "Upper Body": [
            {"name": "Push-ups", "sets": 3, "reps": "8-10", "rest_seconds": 60},
            {"name": "Band Rows", "sets": 3, "reps": "12", "rest_seconds": 60},
            {"name": "Shoulder Press", "sets": 3, "reps": "10", "rest_seconds": 60}
        ],
        "Lower Body": [
            {"name": "Bodyweight Squats", "sets": 3, "reps": "12-15", "rest_seconds": 60},
            {"name": "Lunges", "sets": 3, "reps": "10 each leg", "rest_seconds": 60},
            {"name": "Glute Bridges", "sets": 3, "reps": "15", "rest_seconds": 45}
        ],
        "Core": [
            {"name": "Plank", "sets": 3, "reps": "30 seconds", "rest_seconds": 45},
            {"name": "Crunches", "sets": 3, "reps": "15", "rest_seconds": 45},
            {"name": "Bird Dogs", "sets": 3, "reps": "10 each side", "rest_seconds": 45}
        ]
    },
    "advanced": {
        "Upper Body": [
            {"name": "Diamond Push-ups", "sets": 4, "reps": "15-20", "rest_seconds": 45},
            {"name": "Pull-ups", "sets": 4, "reps": "8-10", "rest_seconds": 60},
            {"name": "Dips", "sets": 4, "reps": "12-15", "rest_seconds": 60}
        ],
        "Lower Body": [
            {"name": "Jump Squats", "sets": 4, "reps": "20", "rest_seconds": 45},
            {"name": "Bulgarian Split Squats", "sets": 4, "reps": "12 each leg", "rest_seconds": 45},
            {"name": "Box Jumps", "sets": 4, "reps": "15", "rest_seconds": 60}
        ],
        "Core": [
            {"name": "Hanging Leg Raises", "sets": 4, "reps": "15", "rest_seconds": 45},
            {"name": "Russian Twists", "sets": 4, "reps": "20 each side", "rest_seconds": 45},
            {"name": "Ab Wheel Rollouts", "sets": 4, "reps": "12", "rest_seconds": 60}
        ]
    }
}

# Meal database
MEAL_LIBRARY = {
    "beginner": {
        "Breakfast": [
            {"name": "Oatmeal with Banana and Honey", "calories": 350, "protein": 12, "carbs": 65, "fats": 6,
             "description": "1 cup oatmeal, 1 banana, 1 tbsp honey, 1 cup milk"},
            {"name": "Greek Yogurt Parfait", "calories": 300, "protein": 20, "carbs": 45, "fats": 8,
             "description": "1 cup Greek yogurt, mixed berries, granola"}
        ],
        "Lunch": [
            {"name": "Turkey Sandwich", "calories": 400, "protein": 25, "carbs": 45, "fats": 12,
             "description": "Whole grain bread, turkey, lettuce, tomato, mayo"},
            {"name": "Chicken Caesar Salad", "calories": 350, "protein": 30, "carbs": 15, "fats": 20,
             "description": "Romaine lettuce, grilled chicken, Caesar dressing, croutons"}
        ],
        "Dinner": [
            {"name": "Grilled Chicken with Rice", "calories": 450, "protein": 35, "carbs": 55, "fats": 10,
             "description": "6oz chicken breast, 1 cup brown rice, steamed vegetables"},
            {"name": "Baked Salmon with Sweet Potato", "calories": 500, "protein": 40, "carbs": 45, "fats": 15,
             "description": "6oz salmon, 1 medium sweet potato, asparagus"}
        ]
    },
    "advanced": {
        "Breakfast": [
            {"name": "Protein Oatmeal", "calories": 450, "protein": 35, "carbs": 65, "fats": 8,
             "description": "1 cup oatmeal, 1 scoop protein powder, banana, almond butter"},
            {"name": "Egg White Omelet", "calories": 400, "protein": 40, "carbs": 20, "fats": 15,
             "description": "6 egg whites, vegetables, cheese, whole grain toast"}
        ],
        "Lunch": [
            {"name": "Chicken Rice Bowl", "calories": 550, "protein": 45, "carbs": 65, "fats": 12,
             "description": "8oz chicken breast, 1.5 cups brown rice, vegetables, avocado"},
            {"name": "Tuna Pasta Salad", "calories": 500, "protein": 40, "carbs": 60, "fats": 15,
             "description": "2 cans tuna, whole grain pasta, mixed vegetables, olive oil dressing"}
        ],
        "Dinner": [
            {"name": "Steak with Sweet Potato", "calories": 650, "protein": 50, "carbs": 55, "fats": 25,
             "description": "8oz lean steak, large sweet potato, broccoli"},
            {"name": "Turkey Meatballs with Quinoa", "calories": 600, "protein": 45, "carbs": 65, "fats": 20,
             "description": "6oz turkey meatballs, 1.5 cups quinoa, roasted vegetables"}
        ]
    }
}

@app.post("/generate-plan", response_model=WeeklyPlan)
async def generate_weekly_plan(request: WorkoutPlanRequest):
    if request.fitness_level not in ["beginner", "advanced"]:
        raise HTTPException(status_code=400, detail="Invalid fitness level")
    if request.duration_minutes not in [30, 60]:
        raise HTTPException(status_code=400, detail="Invalid duration")
    
    try:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Generate workout plan
    workout_plan = []
    focus_areas = ["Upper Body", "Lower Body", "Core"]
    
    for i in range(5):  # 5 workout days per week
        current_date = start_date + timedelta(days=i)
        day_name = current_date.strftime("%A")
        
        focus_area = focus_areas[i % len(focus_areas)]
        exercises = EXERCISE_LIBRARY[request.fitness_level][focus_area]
        
        # Adjust number of exercises based on duration
        num_exercises = 3 if request.duration_minutes == 30 else 5
        selected_exercises = random.sample(exercises, min(num_exercises, len(exercises)))
        
        calories_burn = random.randint(200, 300) if request.duration_minutes == 30 else random.randint(400, 600)
        
        workout_day = WorkoutDay(
            day=day_name,
            focus_area=focus_area,
            exercises=[Exercise(**ex) for ex in selected_exercises],
            calories_burn_estimate=calories_burn
        )
        workout_plan.append(workout_day)

    # Generate diet plan
    diet_plan = []
    for i in range(7):  # 7 days of meals
        current_date = start_date + timedelta(days=i)
        day_name = current_date.strftime("%A")
        
        daily_meals = []
        total_calories = 0
        
        # Add meals for the day
        for meal_type in ["Breakfast", "Lunch", "Dinner"]:
            meal_options = MEAL_LIBRARY[request.fitness_level][meal_type]
            selected_meal = random.choice(meal_options)
            daily_meals.append(Meal(**selected_meal))
            total_calories += selected_meal["calories"]
        
        diet_day = DietDay(
            day=day_name,
            total_calories=total_calories,
            meals=daily_meals
        )
        diet_plan.append(diet_day)

    return WeeklyPlan(workout_plan=workout_plan, diet_plan=diet_plan)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)