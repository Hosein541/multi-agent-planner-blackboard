# Blackboard Planner

**An intelligent multi-agent Daily Task Manager** built with **Blackboard Architecture** and **LangGraph**.

This system helps users create realistic, prioritized, and motivating daily plans by leveraging specialized agents that collaborate through a shared blackboard.

![Blackboard Planner](https://via.placeholder.com/800x400?text=Blackboard+Planner+Demo)  
*(Add a screenshot or GIF here later)*

---

## ✨ Features

- **Blackboard Architecture**: Multiple specialized agents collaborate via a shared memory (blackboard)
- **Intelligent Controller**: Dynamically decides which agent should act next
- **Specialized Agents**:
  - Energy & Time Estimator
  - Dependency Detector
  - Priority & Eisenhower Matrix Agent
  - Calendar Sync Agent
  - Motivation & Habit Builder
  - Critic Agent
- **Interactive Chat**: Update tasks, energy level, available hours, fixed events, constraints, and get re-generated plans. Anwer question about the plan and general questions.
- **Full Transparency**: See the complete reasoning process on the blackboard
- **Built with Poetry** for clean dependency management

---

## 🛠 Tech Stack

- **Framework**: LangGraph + LangChain
- **LLM**: Google Gemini
- **UI**: Streamlit
- **Dependency Manager**: Poetry

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Hosein541/multi-agent-planner-blackboard.git
cd blackboard-planner
```
### 2. Install Dependencies with Poetry
```bash
poetry install
```
### 3. Run the Application
```bash
poetry run streamlit run app.py
```

## Configuration
You need a Google Gemini API Key.
simply enter it in the Streamlit sidebar.

## Project Structure
```text
Bashblackboard-planner/
├── app.py           # Streamlit UI + Chat Interface
├── board.py         # Blackboard Architecture + LangGraph
├── chat.py          # Chat handler and intent detection
├── pyproject.toml   # Poetry configuration
├── poetry.lock
└── README.md
```

## How It Works

User enters daily tasks, energy level, available hours, fixed events, constraints and goals
Agents collaborate through the Blackboard:
Energy & Time Estimator analyzes your capacity
Dependency Detector finds task relationships
Priority Agent applies Eisenhower Matrix
Calendar Agent checks for conflicts
Motivation Agent adds encouragement and habit building
Critic Agent evaluates the final daily plan

Controller intelligently routes between agents
Final realistic and motivating daily plan is generated
User can chat to modify anything and instantly get an updated plan


## Future Improvements

Google Calendar integration (real sync)
Weekly planning mode
Habit tracking over time
Voice input support
PDF daily planner export


## License
This project is open-sourced under the MIT License.