# streamlit_app.py
import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Workout & Diet Planner", layout="wide")

def create_calendar_view(workout_plan, diet_plan):
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add workout calories burned
    workout_days = [day.day for day in workout_plan]
    calories_burned = [day.calories_burn_estimate for day in workout_plan]
    
    fig.add_trace(
        go.Bar(name="Calories Burned", x=workout_days, y=calories_burned, marker_color='rgb(26, 118, 255)'),
        secondary_y=False,
    )
    
    # Add diet calories
    diet_days = [day.day for day in diet_plan]
    calories_consumed = [day.total_calories for day in diet_plan]
    
    fig.add_trace(
        go.Scatter(name="Calories Consumed", x=diet_days, y=calories_consumed, 
                  line=dict(color='rgb(255, 99, 71)', width=2)),
        secondary_y=True,
    )
    
    # Update layout
    fig.update_layout(
        title="Weekly Calories Overview",
        hovermode='x unified',
        barmode='group',
        height=400
    )
    
    # Update axes labels
    fig.update_yaxes(title_text="Calories Burned", secondary_y=False)
    fig.update_yaxes(title_text="Calories Consumed", secondary_y=True)
    
    return fig

def main():
    st.title("🏋️‍♂️ Workout & Diet Planner")
    
    # Sidebar for inputs
    st.sidebar.header("Plan Parameters")
    
    fitness_level = st.sidebar.selectbox(
        "Select your fitness level:",
        ["beginner", "advanced"]
    )
    
    duration = st.sidebar.selectbox(
        "Workout duration:",
        [30, 60],
        format_func=lambda x: f"{x} minutes"
    )
    
    start_date = st.sidebar.date_input(
        "Start date:",
        min_value=datetime.today(),
        max_value=datetime.today() + timedelta(days=30)
    )
    
    if st.sidebar.button("Generate Plan"):
        # API call
        try:
            response = requests.post(
                "http://localhost:8000/generate-plan",
                json={
                    "fitness_level": fitness_level,
                    "duration_minutes": duration,
                    "start_date": start_date.strftime("%Y-%m-%d")
                }
            )
            
            if response.status_code == 200:
                plan_data = response.json()
                
                # Display overview
                st.header("📊 Weekly Overview")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Total Workout Days",
                        len(plan_data["workout_plan"]),
                        "5 days/week"
                    )
                
                with col2:
                    total_calories_burned = sum(day["calories_burn_estimate"] for day in plan_data["workout_plan"])
                    st.metric(
                        "Estimated Weekly Calories Burn",
                        f"{total_calories_burned:,} kcal"
                    )
                
                # Display calendar view
                st.plotly_chart(create_calendar_view(
                    [type('WorkoutDay', (), day) for day in plan_data["workout_plan"]],
                    [type('DietDay', (), day) for day in plan_data["diet_plan"]]
                ), use_container_width=True)
                
                # Display workout plan
                st.header("💪 Workout Plan")
                for day in plan_data["workout_plan"]:
                    with st.expander(f"{day['day']} - {day['focus_area']}"):
                        exercises_df = pd.DataFrame(day["exercises"])
                        st.dataframe(exercises_df, use_container_width=True)
                        st.caption(f"Estimated calories burn: {day['calories_burn_estimate']} kcal")
                
                # Display diet plan
                st.header("🥗 Diet Plan")
                for day in plan_data["diet_plan"]:
                    with st.expander(f"{day['day']} - {day['total_calories']} kcal"):
                        for meal in day["meals"]:
                            st.subheader(meal["name"])
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("Nutrients:")
                                st.write(f"• Calories: {meal['calories']} kcal")
                                st.write(f"• Protein: {meal['protein']}g")
                                st.write(f"• Carbs: {meal['carbs']}g")
                                st.write(f"• Fats: {meal['fats']}g")
                            
                            with col2:
                                st.write("Description:")
                                st.write(meal["description"])
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()