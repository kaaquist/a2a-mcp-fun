# from langchain_ollama import ChatOllama
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langgraph_supervisor import create_supervisor
from typing import Annotated, Sequence
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio


@tool
def calculator(expression: str) -> str:
    """Evaluates a mathematical expression and returns the result as a string."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


# Create a supervisor workflow with A2A client
async def create_multi_agent_workflow():
    """Create a LangGraph workflow with a supervisor and an A2A client."""
    ## Have tried to use the same OLLAMA - LLM setup but it did fail - seems like the model does not support the multiagent
    ## setup.
    # TODO: find a Ollama model that support the Supervisor Langchain usages of agents.
    # ollama_chat_llm = ChatOllama(
    #     base_url="http://localhost:11435",
    #     model="granite3.2:8b",
    #     temperature=0.2
    # )
    ollama_chat_llm = ChatOpenAI(model="gpt-4o")
    client = MultiServerMCPClient(
        {
            "weather": {
                # Ensure your start your weather server on port 8000
                "url": "http://localhost:8090/sse",
                "transport": "sse",
            }
        }
    )
    weather_tools = await client.get_tools()
    weather_agent = create_react_agent(
        model=ollama_chat_llm,
        tools=weather_tools,
        prompt=(
            "You are a weather agent. \n\n"
            "INSTRUCTIONS:\n"
            "- Assist ONLY with weather-related tasks, DO NOT do anything else\n"
            "- After you're done with your tasks,  respond to the supervisor directly\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        ),
        name="weather_agent",
    )

    # Create a LangChain agent for another role (e.g., math agent)
    math_agent = create_react_agent(
        model=ollama_chat_llm,
        tools=[calculator],
        prompt="You are a math agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with math-related tasks\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text.",
        name="math_agent",
    )

    # Create the supervisor
    supervisor = create_supervisor(
        agents=[math_agent, weather_agent],
        model=ollama_chat_llm,
        prompt=(
            "You are a supervisor managing two agents:\n"
            "- a weather agent. Assign weather-related tasks to this agent\n"
            "- a math agent. Assign math-related tasks to this agent\n"
            "Assign work to one agent at a time, do not call agents in parallel.\n"
            "Do not do any work yourself."
        ),
        # add_handoff_back_messages=True,
        output_mode="full_history",
    )
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.store.memory import InMemoryStore

    checkpointer = InMemorySaver()
    store = InMemoryStore()
    return supervisor.compile(checkpointer=checkpointer, store=store)


async def run():
    import uuid

    # Create and compile the workflow
    graph = await create_multi_agent_workflow()

    # Run the graph with a sample task
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = await graph.ainvoke(
        {
            "messages": [
                HumanMessage(content="Get weather for Paris France and is 3=2?")
            ]
        },
        config,
    )

    # Print the final result
    print("\nFinal Result:")
    for msg in result["messages"]:
        print(f"{msg.name} said:\n\n {msg.content} \n\n {'*'*50}")


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


# Example usage
if __name__ == "__main__":
    main()
