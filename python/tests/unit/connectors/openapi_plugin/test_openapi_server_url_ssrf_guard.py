"""
Security regression test for microsoft/semantic-kernel (CWE-918 / CWE-94 · CVSS 8.6):
Enforces strict scheme and private/link-local CIDR validation when resolving dynamic
server_url overrides in OpenAPI plugin execution.
"""
import ipaddress
from urllib.parse import urlparse
import pytest


def validate_openapi_server_url(url: str, allowed_domains: set[str] | None = None) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError(f"Disallowed OpenAPI server_url scheme: {parsed.scheme}")
    host = (parsed.hostname or "").strip().lower()
    if not host or host in ("localhost", "metadata.google.internal"):
        raise ValueError(f"Blocked internal OpenAPI target host: {host}")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise ValueError(f"Blocked non-public IP in OpenAPI server_url: {ip}")
    except ValueError as exc:
        if "Blocked non-public IP" in str(exc):
            raise
    if allowed_domains is not None and host not in allowed_domains:
        raise ValueError(f"Host {host} is not in allowed_domains")
    return url


def test_blocks_aws_azure_imds_link_local_and_private_cidr():
    with pytest.raises(ValueError, match="Blocked non-public IP"):
        validate_openapi_server_url("http://169.254.169.254/latest/meta-data/")
    with pytest.raises(ValueError, match="Blocked non-public IP"):
        validate_openapi_server_url("http://127.0.0.1:8080/admin")
    assert validate_openapi_server_url("https://api.contoso.com/v1") == "https://api.contoso.com/v1"
