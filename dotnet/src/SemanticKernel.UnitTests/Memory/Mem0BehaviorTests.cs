// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CA1054 // URI-like parameters should not be strings

using System;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Contains tests for the <see cref="Mem0Behavior"/> class.
/// </summary>
public class Mem0BehaviorTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly Mock<MockableMessageHandler> _mockMessageHandler;
    private bool _disposedValue;

    public Mem0BehaviorTests()
    {
        this._mockMessageHandler = new Mock<MockableMessageHandler>() { CallBase = true };
        this._httpClient = new HttpClient(this._mockMessageHandler.Object)
        {
            BaseAddress = new Uri("https://localhost/fakepath")
        };
    }

    [Fact]
    public void ValidatesHttpClientBaseAddress()
    {
        // Arrange
        using var httpClientWithoutBaseAddress = new HttpClient();

        // Act & Assert
        var exception = Assert.Throws<ArgumentException>(() =>
        {
            new Mem0Behavior(httpClientWithoutBaseAddress);
        });

        Assert.Equal("The BaseAddress of the provided httpClient parameter must be set. (Parameter 'httpClient')", exception.Message);
    }

    [Fact]
    public void AIFunctionsAreSetCorrectly()
    {
        // Arrange
        var sut = new Mem0Behavior(this._httpClient, new() { ApplicationId = "test-app-id" });

        // Act
        var aiFunctions = sut.AIFunctions;

        // Assert
        Assert.NotNull(aiFunctions);
        Assert.Empty(aiFunctions);
    }

    [Theory]
    [InlineData(false, "test-thread-id")]
    [InlineData(true, "test-thread-id-1")]
    public async Task PostsMemoriesOnNewMessage(bool scopePerOperationThread, string expectedThreadId)
    {
        // Arrange
        using var httpResponse = new HttpResponseMessage() { StatusCode = System.Net.HttpStatusCode.OK };
        this._mockMessageHandler
            .Setup(x => x.MockableSendAsync(It.IsAny<HttpMethod>(), It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(httpResponse);

        var sut = new Mem0Behavior(this._httpClient, new() { ApplicationId = "test-app-id", AgentId = "test-agent-id", ThreadId = "test-thread-id", UserId = "test-user-id", ScopeToPerOperationThreadId = scopePerOperationThread });

        // Act
        await sut.OnNewMessageAsync("test-thread-id-1", new ChatMessage(ChatRole.User, "Hello, my name is Caoimhe."));

        // Assert
        var expectedPayload = $$"""
            {"app_id":"test-app-id","agent_id":"test-agent-id","run_id":"{{expectedThreadId}}","user_id":"test-user-id","messages":[{"content":"Hello, my name is Caoimhe.","role":"user"}]}
            """;
        this._mockMessageHandler.Verify(x => x.MockableSendAsync(HttpMethod.Post, "https://localhost/v1/memories/", expectedPayload, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Theory]
    [InlineData(false, "test-thread-id", null, "Consider the following memories when answering user questions:{0}Name is Caoimhe")]
    [InlineData(true, "test-thread-id-1", "Custom Prompt:", "Custom Prompt:{0}Name is Caoimhe")]
    public async Task SearchesForMemoriesOnModelInvoke(bool scopePerOperationThread, string expectedThreadId, string? customContextPrompt, string expectedAdditionalInstructions)
    {
        // Arrange
        var expectedResponseString = """
            [{"id":"1","memory":"Name is Caoimhe","hash":"abc123","metadata":null,"score":0.9,"created_at":"2023-01-01T00:00:00Z","updated_at":null,"user_id":"test-user-id","app_id":null,"agent_id":"test-agent-id","session_id":"test-thread-id-1"}]
            """;
        using var httpResponse = new HttpResponseMessage()
        {
            StatusCode = System.Net.HttpStatusCode.OK,
            Content = new StringContent(expectedResponseString, Encoding.UTF8, "application/json")
        };

        this._mockMessageHandler
            .Setup(x => x.MockableSendAsync(It.IsAny<HttpMethod>(), It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(httpResponse);

        var sut = new Mem0Behavior(this._httpClient, new()
        {
            ApplicationId = "test-app-id",
            AgentId = "test-agent-id",
            ThreadId = "test-thread-id",
            UserId = "test-user-id",
            ScopeToPerOperationThreadId = scopePerOperationThread,
            ContextPrompt = customContextPrompt
        });
        await sut.OnThreadCreatedAsync("test-thread-id-1");

        // Act
        var actual = await sut.OnModelInvokeAsync(new[] { new ChatMessage(ChatRole.User, "What is my name?") });

        // Assert
        var expectedPayload = $$"""
            {"app_id":"test-app-id","agent_id":"test-agent-id","run_id":"{{expectedThreadId}}","user_id":"test-user-id","query":"What is my name?"}
            """;
        this._mockMessageHandler.Verify(x => x.MockableSendAsync(HttpMethod.Post, "https://localhost/v1/memories/search/", expectedPayload, It.IsAny<CancellationToken>()), Times.Once);

        Assert.Equal(string.Format(expectedAdditionalInstructions, Environment.NewLine), actual);
    }

    [Theory]
    [InlineData(false, "test-thread-id")]
    [InlineData(true, "test-thread-id-1")]
    public async Task ClearsStoredUserFacts(bool scopePerOperationThread, string expectedThreadId)
    {
        // Arrange
        using var httpResponse = new HttpResponseMessage() { StatusCode = System.Net.HttpStatusCode.OK };
        this._mockMessageHandler
            .Setup(x => x.MockableSendAsync(It.IsAny<HttpMethod>(), It.IsAny<string>(), null, It.IsAny<CancellationToken>()))
            .ReturnsAsync(httpResponse);

        var sut = new Mem0Behavior(this._httpClient, new() { ApplicationId = "test-app-id", AgentId = "test-agent-id", ThreadId = "test-thread-id", UserId = "test-user-id", ScopeToPerOperationThreadId = scopePerOperationThread });
        await sut.OnThreadCreatedAsync("test-thread-id-1");

        // Act
        await sut.ClearStoredMemoriesAsync();

        // Assert
        var expectedUrl = $"https://localhost/v1/memories/?app_id=test-app-id&agent_id=test-agent-id&run_id={expectedThreadId}&user_id=test-user-id";
        this._mockMessageHandler.Verify(x => x.MockableSendAsync(HttpMethod.Delete, expectedUrl, null, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task ThrowsExceptionWhenThreadIdChangesAfterBeingSet()
    {
        // Arrange
        var sut = new Mem0Behavior(this._httpClient, new() { ScopeToPerOperationThreadId = true });

        // Act
        await sut.OnThreadCreatedAsync("initial-thread-id");

        // Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(async () =>
        {
            await sut.OnThreadCreatedAsync("new-thread-id");
        });

        Assert.Equal("The Mem0Behavior can only be used with one thread at a time when ScopeToPerOperationThreadId is set to true.", exception.Message);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._httpClient.Dispose();
            }

            this._disposedValue = true;
        }
    }

    public void Dispose()
    {
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    public class MockableMessageHandler : DelegatingHandler
    {
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            string? contentString = request.Content is null ? null : await request.Content.ReadAsStringAsync(cancellationToken);
            return await this.MockableSendAsync(request.Method, request.RequestUri?.AbsoluteUri, contentString, cancellationToken);
        }

        public virtual Task<HttpResponseMessage> MockableSendAsync(HttpMethod method, string? absoluteUri, string? content, CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }
}
