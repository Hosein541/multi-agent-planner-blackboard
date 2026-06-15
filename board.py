from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate

# ====================== BLACKBOARD STATE ======================
class BlackboardState(TypedDict):
    user_request: dict           # اطلاعات کاربر (تسک‌ها، انرژی، تقویم و ...)
    blackboard: List[str]        # گزارش‌های Agentها
    available_agents: List[str]
    next_agent: Optional[str]


# ====================== CONTROLLER DECISION ======================
class ControllerDecision(BaseModel):
    next_agent: str = Field(
        description="The name of the next agent to call. Must be one of the available agents or 'FINISH'."
    )
    reasoning: str = Field(description="Brief reason for choosing this agent.")


# ====================== SPECIALIST AGENT FACTORY ======================
def create_blackboard_specialist(persona: str, agent_name: str, llm):
    system_prompt = f"""You are an expert {persona} in a personal task management and daily planning system.
Your job is to contribute specifically and concisely to create the best possible daily plan.
Read the User Request and the current Blackboard carefully.
Provide a useful, structured markdown report.
Always end with: **Report from {agent_name}**"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """User Request:
{user_request}

Current Blackboard:
{blackboard_str}
""")
    ])

    agent = prompt_template | llm

    def specialist_node(state: BlackboardState):
        print(f"--- [Blackboard] AGENT '{agent_name}' is working ---")
        
        # Format user request
        if isinstance(state["user_request"], dict):
            user_req_str = "\n".join([f"{k}: {v}" for k, v in state["user_request"].items()])
        else:
            user_req_str = str(state["user_request"])

        blackboard_str = "\n\n---\n\n".join(state["blackboard"]) if state["blackboard"] else "Blackboard is currently empty."

        try:
            result = agent.invoke({
                "user_request": user_req_str,
                "blackboard_str": blackboard_str
            })
            content = result.content[0]["text"] if hasattr(result, 'content') else str(result)
            report = f"**Report from {agent_name}:**\n\n{content.strip()}"
        except Exception as e:
            report = f"**Report from {agent_name}:**\n\nError: {str(e)}"

        return {"blackboard": state["blackboard"] + [report]}

    return specialist_node


# ====================== CONTROLLER NODE ======================
def create_controller_node(llm):
    def controller_node(state: BlackboardState):
        print("--- CONTROLLER: Analyzing blackboard... ---")
        
        controller_llm = llm.with_structured_output(ControllerDecision)
        
        blackboard_content = "\n\n".join(state['blackboard']) if state['blackboard'] else "Blackboard is empty."
        
        prompt = f"""You are the Controller of Blackboard Planner - an intelligent daily task management system.

**User Request:**
{state['user_request']}

**Current Blackboard:**
---
{blackboard_content}
---

**Available Agents:** {', '.join(state['available_agents'])}

**Decision Rules:**
1. Start with Energy & Time Estimator
2. Then Dependency Detector
3. Then Priority & Eisenhower Agent
4. Then Calendar Sync Agent
5. Use Motivation & Habit Builder near the end
6. Use Critic Agent (if added) before FINISH
7. Only choose FINISH when a complete, realistic and motivating plan is ready.

Choose the single best next agent:"""

        decision = controller_llm.invoke(prompt)
        print(f"--- CONTROLLER decided: {decision.next_agent} | Reason: {decision.reasoning} ---")
        
        return {"next_agent": decision.next_agent}
    
    return controller_node


# ====================== BUILD GRAPH ======================
def build_blackboard_graph(llm):
    builder = StateGraph(BlackboardState)
    
    controller_node = create_controller_node(llm)
    
    # ایجاد Agentها
    energy_agent = create_blackboard_specialist(
        "Energy & Time Estimator", 
        "Energy & Time Estimator", llm
    )
    
    dependency_agent = create_blackboard_specialist(
        "Dependency Detector", 
        "Dependency Detector", llm
    )
    
    priority_agent = create_blackboard_specialist(
        "Priority & Eisenhower Matrix Expert", 
        "Priority & Eisenhower Agent", llm
    )
    
    calendar_agent = create_blackboard_specialist(
        "Calendar Sync & Schedule Optimizer", 
        "Calendar Sync Agent", llm
    )
    
    motivation_agent = create_blackboard_specialist(
        "Motivation & Habit Building Expert", 
        "Motivation & Habit Builder", llm
    )
    
    critic_agent = create_blackboard_specialist(
        "Critical Reviewer who evaluates the final daily plan", 
        "Critic Agent", llm
    )

    # اضافه کردن نودها
    builder.add_node("Controller", controller_node)
    builder.add_node("Energy & Time Estimator", energy_agent)
    builder.add_node("Dependency Detector", dependency_agent)
    builder.add_node("Priority & Eisenhower Agent", priority_agent)
    builder.add_node("Calendar Sync Agent", calendar_agent)
    builder.add_node("Motivation & Habit Builder", motivation_agent)
    builder.add_node("Critic Agent", critic_agent)

    builder.set_entry_point("Controller")

    def route(state: BlackboardState):
        return state["next_agent"]

    agents_map = {
        "Energy & Time Estimator": "Energy & Time Estimator",
        "Dependency Detector": "Dependency Detector",
        "Priority & Eisenhower Agent": "Priority & Eisenhower Agent",
        "Calendar Sync Agent": "Calendar Sync Agent",
        "Motivation & Habit Builder": "Motivation & Habit Builder",
        "Critic Agent": "Critic Agent",
        "FINISH": END
    }

    builder.add_conditional_edges("Controller", route, agents_map)

    # بازگشت به Controller بعد از هر Agent
    for agent in list(agents_map.keys())[:-1]:
        builder.add_edge(agent, "Controller")

    return builder.compile(), list(agents_map.keys())[:-1]