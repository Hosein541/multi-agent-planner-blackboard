import streamlit as st
import time
import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from board import build_blackboard_graph



def extract_between(text, start_phrase, end_phrase=None, include_phrases=True):
    """
    Extract text located between start_phrase and end_phrase.
    
    Args:
        text (str): The full text.
        start_phrase (str): The starting delimiter.
        end_phrase (str, optional): The ending delimiter. If None, extract from start to end of text.
        include_phrases (bool): If True, include the delimiters in the result.
    
    Returns:
        str: Extracted section, or empty string if start not found.
    """
    # Escape regex special characters in phrases
    start_esc = re.escape(start_phrase)
    if end_phrase:
        end_esc = re.escape(end_phrase)
        pattern = f"({start_esc})(.*?)({end_esc})" if include_phrases else f"{start_esc}(.*?){end_esc}"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            if include_phrases:
                return match.group(0)  # full match including delimiters
            else:
                return match.group(1).strip()  # content only
    else:
        # No end phrase: extract from start to the end
        start_idx = text.find(start_phrase)
        if start_idx == -1:
            return ""
        if include_phrases:
            return text[start_idx:]
        else:
            return text[start_idx + len(start_phrase):].strip()
    
    return ""

st.set_page_config(page_title="Blackboard Planner", layout="wide")
st.title("📅 Blackboard Planner")
st.markdown("**Intelligent Daily Task Manager using Blackboard Architecture + LangGraph**")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("🔑 API Settings")
    gemini_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GOOGLE_API_KEY", ""))

    st.header("📝 Daily Information")
    
    tasks = st.text_area(
        "Your Tasks (one per line)",
        placeholder="Prepare presentation for client meeting\nGo to gym\nReply to pending emails\n...",
        height=200
    )
    
    energy_level = st.selectbox(
        "Today's Energy Level",
        ["High - Full of energy all day", 
         "Medium - Good in morning, drops in afternoon", 
         "Low - Need to be careful with energy"]
    )
    
    available_hours = st.text_input("Available Working Hours", "8:00 AM - 6:00 PM")
    
    fixed_events = st.text_area(
        "Fixed Events / Appointments",
        placeholder="Team meeting 11:00 AM - 12:00 PM\nDoctor appointment at 4:00 PM",
        height=120
    )
    
    constraints = st.text_area(
        "Constraints & Preferences",
        placeholder="I want to sleep before 11 PM\nNo heavy work after 7 PM\nPrefer deep work in morning",
        height=100
    )
    
    goals = st.text_area(
        "Today's Main Goals",
        placeholder="Finish important deliverables\nExercise\nMaintain work-life balance",
        height=100
    )

    start_button = st.button("🚀 Generate Daily Plan", type="primary", use_container_width=True)

# ====================== MAIN AREA ======================
recipe_report = st.container()
status_placeholder = st.empty()
blackboard_container = st.container()
final_plan_placeholder = st.empty()

if start_button and gemini_key:
    # Initialize LLM
    if "llm" not in st.session_state:
        st.session_state.llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            google_api_key=gemini_key,
            temperature=0.5,
        )

    # Build Graph (only once)
    if "blackboard_app" not in st.session_state:
        with st.spinner("Building Blackboard Planner..."):
            app, agents = build_blackboard_graph(st.session_state.llm)
            st.session_state.blackboard_app = app
            st.session_state.available_agents = agents

    # Prepare user input
    user_input = {
        "tasks": [task.strip() for task in tasks.split("\n") if task.strip()],
        "energy_level": energy_level,
        "available_hours": available_hours,
        "fixed_events": fixed_events,
        "constraints": constraints,
        "goals": goals,
        "date": "2026-06-16"   # You can make this dynamic later
    }

    initial_state = {
        "user_request": user_input,
        "blackboard": [],
        "available_agents": st.session_state.available_agents,
        "next_agent": None
    }

    # Run the planner
    with blackboard_container:
        st.subheader("📋 Blackboard Progress (Live)")
        bb_expander = st.expander("Show Full Blackboard", expanded=True)
        bb_placeholder = bb_expander.empty()

    state = initial_state.copy()

    try:
        with status_placeholder:
            st.info("🤖 Agents are working on your plan...")

        # for _ in range(25):  # Safety limit

        #     output = st.session_state.blackboard_app.invoke(state)

        #     state = output

        #     reports = state.get("blackboard", [])
        #     with recipe_report:

        #         reports_text = "\n\n---\n\n".join(reports)
        #         recipe = extract_between(reports_text, "Report from Calendar Sync Agent", "Report from Calendar Sync Agent")
        #         recipe = "\n\n---\n\n".join(extract_between(reports_text, "Report from Motivation & Habit Builder:", "Report from Motivation & Habit Builder:"))
        #         if recipe:
        #             st.markdown(recipe)
        #         else :
        #             st.info("No report found starting with '**Report from Recipe Generator**'.")
        #     st.divider()

        #     if reports:
        #         display_text = "\n\n---\n\n".join(reports)
        #         bb_placeholder.markdown(display_text)
        #     else:
        #         bb_placeholder.markdown("*Waiting for blackboard updates...*")

        #     if state.get("next_agent") == "FINISH":
        #         break

        #     time.sleep(0.8)

        # # Final Result
        # with final_plan_placeholder:
        #     st.success("✅ Your Daily Plan is Ready!")
        #     st.subheader("📌 Final Daily Plan")

        #     final_text = "\n\n".join(state.get("blackboard", [])[-5:])  # Last few reports
        #     st.markdown(final_text)

        #     # Download Button
        #     st.download_button(
        #         label="📥 Download Plan as Markdown",
        #         data=final_text,
        #         file_name="blackboard_daily_plan.md",
        #         mime="text/markdown"
        #     )
        for _ in range(25):
            output = st.session_state.blackboard_app.invoke(state)
            state = output

            # Build the blackboard display
            reports = state.get("blackboard", [])
            with recipe_report:

                reports_text = "\n\n---\n\n".join(reports)
                recipe = extract_between(reports_text, "Report from Calendar Sync Agent", "Report from Calendar Sync Agent")
                recipe = recipe + extract_between(reports_text, "Report from Motivation & Habit Builder", "Report from Motivation & Habit Builder")

                if recipe:
                    st.markdown(recipe)
                else :
                    st.info("No report found starting with Report from Calendar Sync Agent.")
            st.divider()

            if reports:
                display_text = "\n\n---\n\n".join(reports)
                bb_placeholder.markdown(display_text)
            else:
                bb_placeholder.markdown("*Waiting for blackboard updates...*")

            if state.get("next_agent") == "FINISH":
                break
            time.sleep(0.7)

        # Final Result
        with final_plan_placeholder:
            st.success("✅ Your Final Plan is Ready!")
            st.subheader("🍽 Final Daily Plan")

            final_text = "\n\n".join(state.get("blackboard", [])[-4:])  # last few reports
            st.markdown(final_text)

            # Download Button
            st.download_button(
                label="📥 Download Plan",
                data=final_text,
                file_name="blackboard_daily_plan.md",
                mime="text/markdown"
            )
            # if st.button("🔄 Generate New Plan"):
            #     st.session_state.clear()
            #     st.rerun()

    except Exception as e:
        st.error(f"Error occurred: {str(e)}")

else:
    st.info("👈 Please enter your Gemini API key and daily tasks to generate your plan.")

# Footer
st.caption("Blackboard Planner — Powered by Blackboard Architecture + LangGraph")