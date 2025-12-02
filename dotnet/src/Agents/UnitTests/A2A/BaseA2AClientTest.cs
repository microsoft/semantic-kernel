// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using A2A;

namespace SemanticKernel.Agents.UnitTests.A2A;

public class BaseA2AClientTest : IDisposable
{
    internal MultipleHttpMessageHandlerStub MessageHandlerStub { get; }
    internal HttpClient HttpClient { get; }
    internal A2AClient Client { get; }

    internal BaseA2AClientTest()
    {
        this.MessageHandlerStub = new MultipleHttpMessageHandlerStub();
        this.HttpClient = new HttpClient(this.MessageHandlerStub, disposeHandler: false);
        this.Client = new A2AClient(new Uri("http://127.0.0.1/"), this.HttpClient);
    }

    /// <inheritdoc />
    public void Dispose()
    {
        this.MessageHandlerStub.Dispose();
        this.HttpClient.Dispose();

        GC.SuppressFinalize(this);
    }

    protected async Task<AgentCard> CreateAgentCardAsync()
    {
        var capabilities = new AgentCapabilities()
        {
            Streaming = false,
            PushNotifications = false,
        };

        var invoiceQuery = new AgentSkill()
        {
            Id = "id_invoice_agent",
            Name = "InvoiceQuery",
            Description = "Handles requests relating to invoices.",
            Tags = ["invoice", "semantic-kernel"],
            Examples =
            [
                "List the latest invoices for Contoso.",
            ],
        };

        return new AgentCard()
        {
            Name = "InvoiceAgent",
            Description = "Handles requests relating to invoices.",
            Url = "http://127.0.0.1/5000",
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }
}
