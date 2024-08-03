// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.SemanticKernel.Agents.OpenAI.Azure;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Azure;

/// <summary>
/// Unit testing of <see cref="AddHeaderRequestPolicy"/>.
/// </summary>
public class AddHeaderRequestPolicyTests
{
    /// <summary>
    /// Verify behavior of <see cref="AddHeaderRequestPolicy"/>.
    /// </summary>
    [Fact]
    public void VerifyAddHeaderRequestPolicyExecution()
    {
        using HttpClientTransport clientTransport = new();
        HttpPipeline pipeline = new(clientTransport);

        HttpMessage message = pipeline.CreateMessage();

        AddHeaderRequestPolicy policy = new(headerName: "testname", headerValue: "testvalue");
        policy.OnSendingRequest(message);

        Assert.Single(message.Request.Headers);
        HttpHeader header = message.Request.Headers.Single();
        Assert.Equal("testname", header.Name);
        Assert.Equal("testvalue", header.Value);
    }
}
