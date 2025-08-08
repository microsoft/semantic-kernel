// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.A2A;

/// <summary>
/// Tests for the <see cref="A2AAgent"/> class.
/// </summary>
public sealed class A2AAgentTests : BaseA2AClientTest
{
    /// <summary>
    /// Tests that the constructor verifies parameters and throws <see cref="ArgumentNullException"/> when necessary.
    /// </summary>
    [Fact]
    public void ConstructorShouldVerifyParams()
    {
        using var httpClient = new HttpClient();

        // Arrange & Act & Assert
        Assert.Throws<ArgumentNullException>(() => new A2AAgent(null!, new()));
        Assert.Throws<ArgumentNullException>(() => new A2AAgent(this.Client, null!));
    }

    [Fact]
    public async Task VerifyConstructor()
    {
        // Arrange & Act
        var agent = new A2AAgent(this.Client, await this.CreateAgentCardAsync());

        // Assert
        Assert.NotNull(agent);
        Assert.Equal("InvoiceAgent", agent.Name);
        Assert.Equal("Handles requests relating to invoices.", agent.Description);
    }

    [Fact]
    public async Task VerifyInvokeAsync()
    {
        // Arrange
        this.MessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(InvokeResponse, Encoding.UTF8, "application/json") }
        );
        var agent = new A2AAgent(this.Client, await this.CreateAgentCardAsync());

        // Act
        var responseItems = agent.InvokeAsync("List the latest invoices for Contoso?");

        // Assert
        Assert.NotNull(responseItems);
        var items = await responseItems!.ToListAsync<AgentResponseItem<ChatMessageContent>>();
        Assert.Single(items);
        Assert.StartsWith("Here are the latest invoices for Contoso:", items[0].Message.Content);
    }

    [Fact]
    public async Task VerifyInvokeStreamingAsync()
    {
        // Arrange
        this.MessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(InvokeResponse, Encoding.UTF8, "application/json") }
        );
        var agent = new A2AAgent(this.Client, await this.CreateAgentCardAsync());

        // Act
        var responseItems = agent.InvokeStreamingAsync("List the latest invoices for Contoso?");

        // Assert
        Assert.NotNull(responseItems);
        var items = await responseItems!.ToListAsync<AgentResponseItem<StreamingChatMessageContent>>();
        Assert.Single(items);
        Assert.StartsWith("Here are the latest invoices for Contoso:", items[0].Message.Content);
    }

    #region private
    private const string InvokeResponse =
        """
        {"jsonrpc":"2.0","id":"ce7a5ef6-1078-4b6e-ad35-a8bfa6743c5d","result":{"kind":"task","id":"8d328159-ca63-4ce8-b416-4bcf69f9e119","contextId":"496a4a95-392b-4c04-a517-9a043b3f7565","status":{"state":"completed","timestamp":"2025-06-20T09:42:49.4013958Z"},"artifacts":[{"artifactId":"","parts":[{"kind":"text","text":"Here are the latest invoices for Contoso:\n\n1. Invoice ID: INV789, Date: 2025-06-18\n   Products: T-Shirts (150 units at $10.00), Hats (200 units at $15.00), Glasses (300 units at $5.00)\n\n2. Invoice ID: INV666, Date: 2025-06-15\n   Products: T-Shirts (2500 units at $8.00), Hats (1200 units at $10.00), Glasses (1000 units at $6.00)\n\n3. Invoice ID: INV999, Date: 2025-05-17\n   Products: T-Shirts (1400 units at $10.50), Hats (1100 units at $9.00), Glasses (950 units at $12.00)\n\n4. Invoice ID: INV333, Date: 2025-05-13\n   Products: T-Shirts (400 units at $11.00), Hats (600 units at $15.00), Glasses (700 units at $5.00)\n\nIf you need more details on any specific invoice, please let me know!"}]}],"history":[{"role":"user","parts":[{"kind":"text","text":"List the latest invoices for Contoso?"}],"messageId":"80a26c0f-2262-4d0f-8e7d-51ac4046173b"}]}}
        """;
    #endregion
}
