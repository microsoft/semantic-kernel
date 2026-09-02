"""DNS-AID plugin for Microsoft Semantic Kernel."""

from semantic_kernel.functions import kernel_function


class DnsAidPlugin:
    """DNS-AID plugin for Microsoft Semantic Kernel.

    Provides agent discovery, publishing, and unpublishing via DNS-AID.
    """

    def __init__(self, backend_name: str | None = None, backend=None):
        from dns_aid.integrations import DnsAidOperations

        self._ops = DnsAidOperations(backend_name=backend_name, backend=backend)

    @kernel_function(
        name="discover_agents",
        description="Discover AI agents at a domain via DNS-AID SVCB records.",
    )
    async def discover_agents(
        self,
        domain: str,
        protocol: str | None = None,
        name: str | None = None,
        require_dnssec: bool = False,
    ) -> str:
        """Discover AI agents at a domain via DNS-AID SVCB records."""
        return await self._ops.discover_async(
            domain=domain,
            protocol=protocol,
            name=name,
            require_dnssec=require_dnssec,
        )

    @kernel_function(
        name="publish_agent",
        description="Publish an AI agent to DNS via DNS-AID SVCB records.",
    )
    async def publish_agent(
        self,
        name: str,
        domain: str,
        protocol: str = "mcp",
        endpoint: str = "",
        port: int = 443,
        capabilities: list[str] | None = None,
        version: str = "1.0.0",
        description: str | None = None,
        ttl: int = 3600,
    ) -> str:
        """Publish an AI agent to DNS via DNS-AID SVCB records."""
        return await self._ops.publish_async(
            name=name,
            domain=domain,
            protocol=protocol,
            endpoint=endpoint,
            port=port,
            capabilities=capabilities,
            version=version,
            description=description,
            ttl=ttl,
        )

    @kernel_function(
        name="unpublish_agent",
        description="Remove an AI agent from DNS via DNS-AID SVCB records.",
    )
    async def unpublish_agent(
        self,
        name: str,
        domain: str,
        protocol: str = "mcp",
    ) -> str:
        """Remove an AI agent from DNS via DNS-AID SVCB records."""
        return await self._ops.unpublish_async(
            name=name,
            domain=domain,
            protocol=protocol,
        )
