# Copyright (c) Microsoft. All rights reserved.

import os

from agents.copilot_studio.copilot_agent import CopilotAgent
from agents.copilot_studio.directline_client import DirectLineClient
from dotenv import load_dotenv

load_dotenv(override=True)


class BrandAuditor(CopilotAgent):
    """
    Brand auditor agent that ensures all messaging aligns with the brand's identity.
    Evaluates taglines for alignment with brand voice, values and target audience.
    Initializes a DirectLine client configured for the agent instance.
    """

    def __init__(self):
        directline_endpoint = os.getenv("DIRECTLINE_ENDPOINT")
        copilot_agent_secret = os.getenv("AUDITOR_AGENT_SECRET")
        
        if not directline_endpoint or not copilot_agent_secret:
            raise ValueError("DIRECTLINE_ENDPOINT and AUDITOR_AGENT_SECRET must be set in environment variables.")

        directline_client = DirectLineClient(
            directline_endpoint=directline_endpoint,
            copilot_agent_secret=copilot_agent_secret,
        )

        super().__init__(
            id="brand_auditor",
            name="brand_auditor",
            description=(
                "Brand compliance specialist ensuring messaging aligns with a modern wellness "
                "company's identity, values, and audience."
            ),
            directline_client=directline_client,
        )
