import os

from dotenv import load_dotenv

from copilot_studio.copilot_agent import CopilotAgent
from copilot_studio.directline_client import DirectLineClient

load_dotenv(override=True)

class ProductAdvisor(CopilotAgent):
    """
    Template for instantiating Copilot Studio agents with agent-specific secrets from environment variables.  
    Initializes a DirectLine client configured for each agent instance.
    """

    def __init__(self):
        directline_endpoint = os.getenv("DIRECTLINE_ENDPOINT")
        copilot_agent_secret = os.getenv("PRODUCT_ADVISOR_AGENT_SECRET")
        
        if not directline_endpoint or not copilot_agent_secret:
            raise ValueError("DIRECTLINE_ENDPOINT and PRODUCT_ADVISOR_AGENT_SECRET must be set in environment variables.")

        directline_client = DirectLineClient(
            directline_endpoint=directline_endpoint,
            copilot_agent_secret=copilot_agent_secret,
        )

        super().__init__(
            id="product_advisor",
            name="product_advisor",
            description="An agent that helps Small and Medium Business (SMB) users find the right financial products based on their needs.",
            directline_client=directline_client,
        )
