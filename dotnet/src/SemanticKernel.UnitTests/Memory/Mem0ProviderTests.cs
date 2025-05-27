// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CA1054 // URI-like parameters should not be strings

using System;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Contains tests for the <see cref="Mem0Provider"/> class.
/// </summary>
public class Mem0ProviderTests : IDisposable
{
    private readonly Mock<ILogger<Mem0Provider>> _loggerMock;
    private readonly Mock<ILoggerFactory> _loggerFactoryMock;
    private readonly HttpClient _httpClient;
    private readonly Mock<MockableMessageHandler> _mockMessageHandler;
    private bool _disposedValue;

    public Mem0ProviderTests()
    {
        this._loggerMock = new();
        this._loggerFactoryMock = new();
        this._loggerFactoryMock
            .Setup(f => f.CreateLogger(It.IsAny<string>()))
            .Returns(this._loggerMock.Object);
        this._loggerFactoryMock
            .Setup(f => f.CreateLogger(typeof(Mem0Provider).FullName!))
            .Returns(this._loggerMock.Object);

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
            new Mem0Provider(httpClientWithoutBaseAddress);
        });

        Assert.Equal("The BaseAddress of the provided httpClient parameter must be set. (Parameter 'httpClient')", exception.Message);
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

        var sut = new Mem0Provider(this._httpClient, options: new() { ApplicationId = "test-app-id", AgentId = "test-agent-id", ThreadId = "test-thread-id", UserId = "test-user-id", ScopeToPerOperationThreadId = scopePerOperationThread });

        // Act
        await sut.MessageAddingAsync("test-thread-id-1", new ChatMessage(ChatRole.User, "Hello, my name is Caoimhe."));

        // Assert
        var expectedPayload = $$"""
            {"app_id":"test-app-id","agent_id":"test-agent-id","run_id":"{{expectedThreadId}}","user_id":"test-user-id","messages":[{"content":"Hello, my name is Caoimhe.","role":"user"}]}
            """;
        this._mockMessageHandler.Verify(x => x.MockableSendAsync(HttpMethod.Post, "https://localhost/v1/memories/", expectedPayload, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Theory]
    [InlineData(false, "test-thread-id", null, "## Memories\nConsider the following memories when answering user questions:\nName is Caoimhe", true)]
    [InlineData(true, "test-thread-id-1", "Custom Prompt:", "Custom Prompt:\nName is Caoimhe", false)]
    public async Task SearchesForMemoriesOnModelInvoke(bool scopePerOperationThread, string expectedThreadId, string? customContextPrompt, string expectedAdditionalInstructions, bool withLogging)
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

        var sut = new Mem0Provider(
            this._httpClient,
            withLogging ? this._loggerFactoryMock.Object : null,
            options: new()
            {
                ApplicationId = "test-app-id",
                AgentId = "test-agent-id",
                ThreadId = "test-thread-id",
                UserId = "test-user-id",
                ScopeToPerOperationThreadId = scopePerOperationThread,
                ContextPrompt = customContextPrompt
            });
        await sut.ConversationCreatedAsync("test-thread-id-1");

        // Act
        var actual = await sut.ModelInvokingAsync(new[] { new ChatMessage(ChatRole.User, "What is my name?") });

        // Assert
        var expectedPayload = $$"""
            {"app_id":"test-app-id","agent_id":"test-agent-id","run_id":"{{expectedThreadId}}","user_id":"test-user-id","query":"What is my name?"}
            """;
        this._mockMessageHandler.Verify(x => x.MockableSendAsync(HttpMethod.Post, "https://localhost/v1/memories/search/", expectedPayload, It.IsAny<CancellationToken>()), Times.Once);

        Assert.Equal(expectedAdditionalInstructions, actual.Instructions);

        if (withLogging)
        {
            this._loggerMock.Verify(
                l => l.Log(
                    LogLevel.Information,
                    It.IsAny<EventId>(),
                    It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("Mem0Behavior: Retrieved 1 memories from mem0.")),
                    It.IsAny<Exception?>(),
                    It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
                Times.AtLeastOnce);

            this._loggerMock.Verify(
                l => l.Log(
                    LogLevel.Trace,
                    It.IsAny<EventId>(),
                    It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("Mem0Behavior:\nInput messages:What is my name?\nOutput context instructions:\n## Memories\nConsider the following memories when answering user questions:\nName is Caoimhe")),
                    It.IsAny<Exception?>(),
                    It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
                Times.AtLeastOnce);
        }
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

        var sut = new Mem0Provider(this._httpClient, options: new() { ApplicationId = "test-app-id", AgentId = "test-agent-id", ThreadId = "test-thread-id", UserId = "test-user-id", ScopeToPerOperationThreadId = scopePerOperationThread });
        await sut.ConversationCreatedAsync("test-thread-id-1");

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
        var sut = new Mem0Provider(this._httpClient, options: new() { ScopeToPerOperationThreadId = true });

        // Act
        await sut.ConversationCreatedAsync("initial-thread-id");

        // Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(async () =>
        {
            await sut.ConversationCreatedAsync("new-thread-id");
        });

        Assert.Equal("The Mem0Provider can only be used with one thread at a time when ScopeToPerOperationThreadId is set to true.", exception.Message);
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
