import os
import requests
from typing import Annotated
from semantic_kernel.functions import kernel_function

class WarpPayPlugin:
    """
    Semantic Kernel plugin for WarpPay402 monetized Web3 Oracles.
    Executes pay-per-use M2M tools monetized via the x402 V2 protocol.
    """

    def __init__(self, private_key: str = None, paymaster_rpc: str = "https://api.warppay402.com/api/v1/paymaster/rpc"):
        self.private_key = private_key or os.getenv("AGENT_PRIVATE_KEY")
        self.paymaster_rpc = paymaster_rpc
        self.base_url = "https://api.warppay402.com"

    @kernel_function(
        description="Resolves real-time power grid, ISP broadband, and cellular network outages by ZIP code ($0.002 USDC).",
        name="outage_oracle"
    )
    def outage_oracle(
        self,
        zip_code: Annotated[str, "5-digit US ZIP code to query for active outages"]
    ) -> str:
        url = f"{self.base_url}/api/v1/tools/outage-oracle"
        payload = {"zipCode": zip_code}
        response = requests.post(url, json=payload)
        return response.text

    @kernel_function(
        description="Fetches live atmospheric conditions, wind speed, visibility, and flight safety clearances ($0.001 USDC).",
        name="weather_oracle"
    )
    def weather_oracle(
        self,
        latitude: Annotated[float, "Target latitude coordinate"],
        longitude: Annotated[float, "Target longitude coordinate"]
    ) -> str:
        url = f"{self.base_url}/api/v1/tools/weather-oracle"
        payload = {"latitude": latitude, "longitude": longitude}
        response = requests.post(url, json=payload)
        return response.text

    @kernel_function(
        description="Fetches top live Aerodrome DEX yield pools, APYs, TVL, and Base EVM pool addresses ($0.003 USDC).",
        name="get_aerodrome_yields"
    )
    def get_aerodrome_yields(self) -> str:
        url = f"{self.base_url}/api/v1/tools/aerodrome-yields"
        response = requests.get(url)
        return response.text
