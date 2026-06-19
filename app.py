import os
import re
import time
import streamlit as st
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI

from chat import handle_chat_message
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


        for _ in range(25):
            output = st.session_state.blackboard_app.invoke(state)
            state = output
            st.session_state.current_state = state

            # Build the blackboard display
            reports = state.get("blackboard", [])
            with recipe_report:

                reports_text = "\n\n---\n\n".join(reports)
                recipe = extract_between(reports_text, "Report from Calendar Sync Agent", "Report from Calendar Sync Agent")
                recipe = recipe + extract_between(reports_text, "Report from Motivation & Habit Builder", "Report from Motivation & Habit Builder")
                

                if recipe:
                    st.markdown(recipe)
                    st.session_state.final_text = recipe
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

            final_text = "\n\n".join(state.get("blackboard", [])[-4:])  # last few reports


            # Download Button
            st.download_button(
                label="📥 Download Plan",
                data=final_text,
                file_name="blackboard_daily_plan.md",
                mime="text/markdown"
            )
            report_filename = f"daily_palnner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(final_text)
            st.info(f"📁 Report saved locally as: **`{report_filename}`**")
            st.session_state.report_filename = report_filename

        st.session_state.planner_ready = True
        st.session_state.counter = 0
    except Exception as e:
        st.error(f"Error occurred: {str(e)}")

if st.session_state.get("planner_ready", False):
    if st.session_state.counter > 0:
        st.markdown(st.session_state.final_text)
        st.download_button(
            label="📥 Download Plan",
            data=st.session_state.final_text,
            key=15,
            file_name="blackboard_daily_plan.md",
            mime="text/markdown"
        )

        st.info(f"📁 Report saved locally as: **`{st.session_state.report_filename}`**")
    st.session_state.counter +=1
    st.subheader("💬 Chat with Your Finance Advisor")

    #chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            st.markdown(msg.get("agent_output", ""))
            if msg.get("output_path"):
                report_filename = msg.get("output_path", "")
                st.info(f"📁 Report saved locally as: **`{report_filename}`**")

    # recieve user question
    question = st.chat_input("Ask something about your plan...")

    if question:
        # add user message to the chat history
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, state, output_type = handle_chat_message(
                    user_message=question,   # ← اصلاح مهم
                    current_state=st.session_state.current_state,
                    finance_advisor=st.session_state.blackboard_app,
                    llm=st.session_state.llm,
                )
                st.session_state.current_state = state
                st.markdown(response)

                if output_type:
                    st.subheader("📌 Final Recommendation")
                    final_output_text = "\n\n".join(state.get("blackboard", [])[-4:])

                    recipe = extract_between(final_output_text, "Report from Calendar Sync Agent", "Report from Calendar Sync Agent")
                    recipe = recipe + extract_between(final_output_text, "Report from Motivation & Habit Builder", "Report from Motivation & Habit Builder")
                    
                    st.markdown(recipe)
                    # save file and download button
                    final_text = "# Blackboard Advisor - Full Report\n\n" + final_output_text
                    report_filename = f"daily_palnner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

                    with open(report_filename, "w", encoding="utf-8") as f:
                        f.write(final_text)
                    
                    st.info(f"📁 Report saved locally as: **`{report_filename}`**")
                    st.download_button(
                        label="📥 Download Plan",
                        key=2,
                        data=final_text,
                        file_name="blackboard_daily_plan.md",
                        mime="text/markdown"
                    )
        if output_type:
            st.session_state.chat_history.append({"role": "assistant", "content": response, "agent_output":final_output_text, "output_path":report_filename})
        else : 
            st.session_state.chat_history.append({"role": "assistant", "content": response})


else:
    st.info("👈 Please enter your Gemini API key and daily tasks to generate your plan.")

# Footer
st.caption("Blackboard Planner — Powered by Blackboard Architecture + LangGraph")