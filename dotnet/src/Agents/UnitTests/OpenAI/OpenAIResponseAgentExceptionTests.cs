// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Xunit;
using OpenAI;
using OpenAI.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Tests for the exception handling logic in OpenAIResponseAgent.
/// Verifies that provider exceptions are wrapped in KernelException.
/// </summary>
public class OpenAIResponseAgentExceptionTests : BaseOpenAIResponseClientTest
{
    private const string AgentName = "TestAgent";

    /// <summary>
    /// Verifies that InvokeAsync wraps provider exceptions in a KernelException.
    /// </summary>
    [Fact]
    public async Task InvokeAsync_WhenProviderFails_ShouldThrowKernelExceptionAsync()
    {
        // Arrange
        var ex = new HttpRequestException("HTTP 429 Rate limit exceeded");
        var agent = CreateAgentWithThrowingHandler(ex);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<KernelException>(async () =>
        {
            await foreach (var item in agent.InvokeAsync("Hello"))
            {
                // Enumerate to trigger lazy execution
            }
        });

        Assert.Contains($"OpenAI provider error for agent '{AgentName}':", exception.Message);
        Assert.NotNull(exception.InnerException);
        Assert.Contains("HTTP 429 Rate limit exceeded", exception.ToString());
    }

    /// <summary>
    /// Verifies that InvokeStreamingAsync wraps provider exceptions in a KernelException.
    /// </summary>
    [Fact]
    public async Task InvokeStreamingAsync_WhenProviderFails_ShouldThrowKernelExceptionAsync()
    {
        // Arrange
        var ex = new HttpRequestException("HTTP 500 Internal Server Error");
        var agent = CreateAgentWithThrowingHandler(ex);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<KernelException>(async () =>
        {
            await foreach (var item in agent.InvokeStreamingAsync("Hello"))
            {
                // Enumerate to trigger lazy execution
            }
        });

        Assert.Contains($"OpenAI provider error for agent '{AgentName}' during streaming:", exception.Message);
        Assert.NotNull(exception.InnerException);
        Assert.Contains("HTTP 500 Internal Server Error", exception.ToString());
    }

    private OpenAIResponseAgent CreateAgentWithThrowingHandler(Exception exceptionToThrow)
    {
#pragma warning disable CA2000 // Dispose objects before losing scope
        var handler = new ThrowingHttpMessageHandler(exceptionToThrow);
        var httpClient = new HttpClient(handler);
        var clientOptions = new OpenAIClientOptions()
        {
            Transport = new HttpClientPipelineTransport(httpClient)
        };
        var client = new ResponsesClient(new ApiKeyCredential("apiKey"), clientOptions);
        return new OpenAIResponseAgent(client) { Name = AgentName };
#pragma warning restore CA2000 // Dispose objects before losing scope
    }

    private sealed class ThrowingHttpMessageHandler(Exception exceptionToThrow) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            return Task.FromException<HttpResponseMessage>(exceptionToThrow);
        }
    }
}
