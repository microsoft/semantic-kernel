import os

from agents.copilot_studio.copilot_agent import CopilotAgent
from agents.copilot_studio.directline_client import DirectLineClient
from dotenv import load_dotenv

load_dotenv(override=True)


class TaglineGenerator(CopilotAgent):
    """
    Tagline generator agent that creates witty, impactful taglines that resonate with modern consumers.
    Provides a single tagline at a time based on product descriptions or feedback.
    Initializes a DirectLine client configured for the agent instance.
    """

    def __init__(self):
        directline_endpoint = os.getenv("DIRECTLINE_ENDPOINT")
        copilot_agent_secret = os.getenv("TAGLINE_AGENT_SECRET")
        
        if not directline_endpoint or not copilot_agent_secret:
            raise ValueError("DIRECTLINE_ENDPOINT and TAGLINE_AGENT_SECRET must be set in environment variables.")

        directline_client = DirectLineClient(
            directline_endpoint=directline_endpoint,
            copilot_agent_secret=copilot_agent_secret,
        )

        super().__init__(
            id="tagline_generator",
            name="tagline_generator",
            description="Creative copywriter that generates witty, impactful taglines for modern consumers while adapting to brand voice and audience needs.",
            directline_client=directline_client,
        )