# Copyright (c) Microsoft. All rights reserved.

"""Nory x402 Payment Plugin for Semantic Kernel.

A plugin that enables AI agents to make payments using the x402 HTTP protocol.
Supports Solana and 7 EVM chains with sub-400ms settlement.
"""

from typing import Annotated

import aiohttp

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel

NORY_API_BASE = "https://noryx402.com"


class NoryX402Plugin(KernelBaseModel):
    """A plugin that provides x402 payment functionality via Nory.

    Enables AI agents to make payments using the x402 HTTP payment protocol.
    Supports Solana and 7 EVM chains (Base, Polygon, Arbitrum, Optimism,
    Avalanche, Sei, IoTeX) with sub-400ms settlement times.

    Usage:
        kernel.add_plugin(NoryX402Plugin(), "nory")

        # With API key for authenticated endpoints:
        kernel.add_plugin(NoryX402Plugin(api_key="your-api-key"), "nory")

    Examples:
        {{nory.get_payment_requirements "/api/premium/data" "0.10"}}
        {{nory.settle_payment $payload}}
        {{nory.health_check}}
    """

    api_key: str | None = None
    """Nory API key for authenticated endpoints. Optional for public endpoints."""

    def _get_headers(self, with_json: bool = False) -> dict[str, str]:
        """Get request headers with optional auth."""
        headers: dict[str, str] = {}
        if with_json:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @kernel_function(
        name="get_payment_requirements",
        description="Get x402 payment requirements for accessing a paid resource. Use this when you encounter an HTTP 402 Payment Required response.",
    )
    async def get_payment_requirements(
        self,
        resource: Annotated[str, "The resource path requiring payment (e.g., /api/premium/data)"],
        amount: Annotated[str, "Amount in human-readable format (e.g., '0.10' for $0.10 USDC)"],
        network: Annotated[
            str | None,
            "Preferred blockchain network (solana-mainnet, base-mainnet, polygon-mainnet, etc.)",
        ] = None,
    ) -> str:
        """Get payment requirements for a resource.

        Returns amount, supported networks, and wallet address needed to make a payment.

        Args:
            resource: The resource path requiring payment.
            amount: Amount in human-readable format.
            network: Preferred blockchain network (optional).

        Returns:
            JSON string with payment requirements.
        """
        params = {"resource": resource, "amount": amount}
        if network:
            params["network"] = network

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{NORY_API_BASE}/api/x402/requirements",
                params=params,
                headers=self._get_headers(),
                raise_for_status=True,
            ) as response:
                return await response.text()

    @kernel_function(
        name="verify_payment",
        description="Verify a signed payment transaction before settlement. Use this to validate that a payment is correct before submitting to blockchain.",
    )
    async def verify_payment(
        self,
        payload: Annotated[str, "Base64-encoded payment payload containing signed transaction"],
    ) -> str:
        """Verify a signed payment transaction.

        Validates that a payment transaction is correct before submitting
        it to the blockchain.

        Args:
            payload: Base64-encoded payment payload.

        Returns:
            JSON string with verification result including validity and payer info.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{NORY_API_BASE}/api/x402/verify",
                json={"payload": payload},
                headers=self._get_headers(with_json=True),
                raise_for_status=True,
            ) as response:
                return await response.text()

    @kernel_function(
        name="settle_payment",
        description="Settle a payment on-chain. Submits a verified payment to the blockchain with ~400ms settlement time.",
    )
    async def settle_payment(
        self,
        payload: Annotated[str, "Base64-encoded payment payload"],
    ) -> str:
        """Settle a payment on-chain.

        Submits a verified payment transaction to the blockchain.
        Settlement typically completes in under 400ms.

        Args:
            payload: Base64-encoded payment payload.

        Returns:
            JSON string with settlement result including transaction ID.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{NORY_API_BASE}/api/x402/settle",
                json={"payload": payload},
                headers=self._get_headers(with_json=True),
                raise_for_status=True,
            ) as response:
                return await response.text()

    @kernel_function(
        name="lookup_transaction",
        description="Look up the status of a previously submitted payment transaction.",
    )
    async def lookup_transaction(
        self,
        transaction_id: Annotated[str, "Transaction ID or signature"],
        network: Annotated[str, "Network where the transaction was submitted"],
    ) -> str:
        """Look up transaction status.

        Check the status of a previously submitted payment.

        Args:
            transaction_id: Transaction ID or signature.
            network: Network where the transaction was submitted.

        Returns:
            JSON string with transaction details including status and confirmations.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{NORY_API_BASE}/api/x402/transactions/{transaction_id}",
                params={"network": network},
                headers=self._get_headers(),
                raise_for_status=True,
            ) as response:
                return await response.text()

    @kernel_function(
        name="health_check",
        description="Check Nory service health and see supported networks.",
    )
    async def health_check(self) -> str:
        """Check Nory service health.

        Verify the payment service is operational and see supported networks.

        Returns:
            JSON string with health status and supported networks.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{NORY_API_BASE}/api/x402/health",
                raise_for_status=True,
            ) as response:
                return await response.text()
