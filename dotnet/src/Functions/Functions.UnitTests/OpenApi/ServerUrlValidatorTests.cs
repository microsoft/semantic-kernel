// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

/// <summary>
/// Unit tests for the IP classification logic that backs the secure-by-default SSRF
/// protection in <see cref="ServerUrlValidator"/>.
/// </summary>
public class ServerUrlValidatorTests
{
    [Theory]
    // IPv4 - loopback
    [InlineData("127.0.0.1", "loopback")]
    [InlineData("127.255.255.254", "loopback")]
    // IPv4 - link-local (cloud metadata)
    [InlineData("169.254.169.254", "link-local")]
    [InlineData("169.254.0.1", "link-local")]
    // IPv4 - RFC1918
    [InlineData("10.0.0.1", "private (RFC1918)")]
    [InlineData("172.16.0.1", "private (RFC1918)")]
    [InlineData("172.31.255.255", "private (RFC1918)")]
    [InlineData("192.168.0.1", "private (RFC1918)")]
    // IPv4 - CGNAT
    [InlineData("100.64.0.1", "carrier-grade NAT")]
    [InlineData("100.127.255.254", "carrier-grade NAT")]
    // IPv4 - reserved / unspecified / multicast / benchmarking
    [InlineData("0.0.0.0", "unspecified")]
    [InlineData("224.0.0.1", "multicast")]
    [InlineData("239.255.255.255", "multicast")]
    [InlineData("240.0.0.1", "reserved")]
    [InlineData("255.255.255.255", "reserved")]
    [InlineData("198.18.0.1", "benchmarking")]
    [InlineData("192.0.2.1", "reserved")]
    [InlineData("198.51.100.1", "reserved")]
    [InlineData("203.0.113.1", "reserved")]
    // IPv6
    [InlineData("::1", "loopback")]
    [InlineData("::", "unspecified")]
    [InlineData("fe80::1", "link-local")]
    [InlineData("fc00::1", "private (IPv6 ULA)")]
    [InlineData("fd00::1", "private (IPv6 ULA)")]
    [InlineData("ff02::1", "multicast")]
    [InlineData("2001:db8::1", "reserved")]
    // IPv4-mapped IPv6 of a private address
    [InlineData("::ffff:127.0.0.1", "loopback")]
    [InlineData("::ffff:169.254.169.254", "link-local")]
    public void ItShouldClassifyNonPublicAddresses(string address, string expectedCategory)
    {
        // Arrange
        var ip = IPAddress.Parse(address);

        // Act
        var blocked = ServerUrlValidator.TryCategorizeNonPublicAddress(ip, out var category);

        // Assert
        Assert.True(blocked, $"Expected {address} to be classified as non-public.");
        Assert.Equal(expectedCategory, category);
    }

    [Theory]
    // Public IPv4
    [InlineData("8.8.8.8")]
    [InlineData("1.1.1.1")]
    [InlineData("93.184.216.34")]
    [InlineData("172.15.255.255")]   // just outside 172.16/12
    [InlineData("172.32.0.1")]       // just outside 172.16/12
    [InlineData("11.0.0.1")]         // just outside 10/8
    [InlineData("192.169.0.1")]      // just outside 192.168/16
    [InlineData("100.63.255.255")]   // just outside CGNAT
    [InlineData("100.128.0.1")]      // just outside CGNAT
    // Public IPv6
    [InlineData("2606:4700:4700::1111")]   // Cloudflare DNS
    public void ItShouldNotBlockPublicAddresses(string address)
    {
        // Arrange
        var ip = IPAddress.Parse(address);

        // Act
        var blocked = ServerUrlValidator.TryCategorizeNonPublicAddress(ip, out _);

        // Assert
        Assert.False(blocked, $"Expected {address} to be treated as public.");
    }

    [Fact]
    public async Task ItShouldRejectLiteralLinkLocalIPv4InUrlAsync()
    {
        // Arrange
        var url = new Uri("https://169.254.169.254/latest/meta-data/");

        // Act
        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ServerUrlValidator.ValidateAsync(url, options: null));

        // Assert
        Assert.Contains("link-local", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItShouldRejectLiteralLoopbackIPv6InUrlAsync()
    {
        var url = new Uri("https://[::1]/");
        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ServerUrlValidator.ValidateAsync(url, options: null));
        Assert.Contains("loopback", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItShouldRejectHttpSchemeByDefaultForNonAllowlistedHostAsync()
    {
        var url = new Uri("http://api.example.com/");
        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ServerUrlValidator.ValidateAsync(url, options: null));
        Assert.Contains("scheme", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItShouldAllowExplicitAllowedBaseUrlEvenForPrivateAddressAsync()
    {
        var url = new Uri("http://192.168.1.100/v1/orders");
        var options = new RestApiOperationServerUrlValidationOptions
        {
            AllowedBaseUrls = [new Uri("http://192.168.1.100/v1")]
        };

        // Should not throw.
        await ServerUrlValidator.ValidateAsync(url, options);
    }

    [Fact]
    public async Task ItShouldAllowPublicHttpsHostByDefaultAsync()
    {
        // 1.1.1.1 is a literal public IP - exercises the validator without DNS.
        var url = new Uri("https://1.1.1.1/");
        await ServerUrlValidator.ValidateAsync(url, options: null);
    }

    [Fact]
    public async Task ItShouldBypassPrivateGateWhenAllowPrivateNetworkAccessTrueAsync()
    {
        var url = new Uri("https://10.0.0.5/");
        var options = new RestApiOperationServerUrlValidationOptions { AllowPrivateNetworkAccess = true };

        await ServerUrlValidator.ValidateAsync(url, options);
    }

    [Fact]
    public async Task ItShouldBlockHostnameResolvingToPrivateIpAsync()
    {
        // Simulates an attacker-controlled hostname (e.g., evil.com) resolving to the
        // cloud metadata address — the most realistic SSRF vector.
        var url = new Uri("https://evil.example.com/latest/meta-data/");
        Task<IPAddress[]> FakeResolver(string _, CancellationToken _1) =>
            Task.FromResult(new[] { IPAddress.Parse("169.254.169.254") });

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ServerUrlValidator.ValidateAsync(url, options: null, dnsResolver: FakeResolver));
        Assert.Contains("link-local", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItShouldBlockHostnameResolvingToLoopbackAsync()
    {
        var url = new Uri("https://attacker.example.com/api");
        Task<IPAddress[]> FakeResolver(string _, CancellationToken _1) =>
            Task.FromResult(new[] { IPAddress.Parse("127.0.0.1") });

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ServerUrlValidator.ValidateAsync(url, options: null, dnsResolver: FakeResolver));
        Assert.Contains("loopback", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItShouldBlockWhenAnyResolvedAddressIsPrivateAsync()
    {
        // DNS rebinding defense: even if one address is public, a private one must block.
        var url = new Uri("https://rebind.example.com/");
        Task<IPAddress[]> FakeResolver(string _, CancellationToken _1) =>
            Task.FromResult(new[]
            {
                IPAddress.Parse("93.184.216.34"),  // public
                IPAddress.Parse("10.0.0.1")        // private
            });

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ServerUrlValidator.ValidateAsync(url, options: null, dnsResolver: FakeResolver));
        Assert.Contains("private", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItShouldAllowHostnameResolvingToPublicIpAsync()
    {
        var url = new Uri("https://api.example.com/");
        Task<IPAddress[]> FakeResolver(string _, CancellationToken _1) =>
            Task.FromResult(new[] { IPAddress.Parse("93.184.216.34") });

        // Should not throw.
        await ServerUrlValidator.ValidateAsync(url, options: null, dnsResolver: FakeResolver);
    }

    [Fact]
    public async Task ItShouldBlockWhenDnsResolutionFailsAsync()
    {
        var url = new Uri("https://unreachable.example.com/");
        Task<IPAddress[]> FakeResolver(string _, CancellationToken _1) =>
            throw new SocketException();

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ServerUrlValidator.ValidateAsync(url, options: null, dnsResolver: FakeResolver));
        Assert.Contains("DNS resolution", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItShouldBlockWhenDnsReturnsEmptyAsync()
    {
        var url = new Uri("https://empty-dns.example.com/");
        Task<IPAddress[]> FakeResolver(string _, CancellationToken _1) =>
            Task.FromResult(Array.Empty<IPAddress>());

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ServerUrlValidator.ValidateAsync(url, options: null, dnsResolver: FakeResolver));
        Assert.Contains("no addresses", ex.Message, StringComparison.OrdinalIgnoreCase);
    }
}
