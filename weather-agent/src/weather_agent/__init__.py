import logging
import click

from google_a2a.common.types import AgentSkill, AgentCapabilities, AgentCard
from google_a2a.common.server import A2AServer
from weather_agent.task_manager import WeatherAgentTaskManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=8001)
@click.option("--ollama-host", default="http://localhost:11434")
@click.option("--ollama-model", default="granite3.2:8b")
def main(host, port, ollama_host, ollama_model):
    skill = AgentSkill(
        id="weather-agent-skill",
        name="Weather Tool",
        description="Return weather forcast for the requested location",
        tags=["weater", "weather-forcast"],
        examples=[
            "The weather in Copenhagen is partly cloudy with a high of 10 and a low of 5 degreese."
        ],
        inputModes=["text"],
        outputModes=["text"],
    )
    logging.info(f"\n\nThe Skills: {skill}")

    capabilities = AgentCapabilities(streaming=False)
    agent_card = AgentCard(
        name="Weather Agent",
        description="This agent provide a weather forcast for a given location",
        url=f"http://{host}:{port}/",
        version="0.1.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=capabilities,
        skills=[skill],
    )
    logging.info(f"\n\nAgent card: {agent_card}")

    task_manager = WeatherAgentTaskManager(
        ollama_host=ollama_host,
        ollama_model=ollama_model,
    )
    server = A2AServer(
        agent_card=agent_card,
        task_manager=task_manager,
        host=host,
        port=port,
    )
    server.start()


if __name__ == "__main__":
    main()
