// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Functions;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class ContextualFunctionProviderTests
{
    private readonly Mock<VectorStore> _vectorStoreMock;
    private readonly Mock<VectorStoreCollection<object, Dictionary<string, object?>>> _collectionMock;

    public ContextualFunctionProviderTests()
    {
        this._vectorStoreMock = new Mock<VectorStore>(MockBehavior.Strict);
        this._collectionMock = new Mock<VectorStoreCollection<object, Dictionary<string, object?>>>(MockBehavior.Strict);

        this._vectorStoreMock
            .Setup(vs => vs.GetDynamicCollection(It.IsAny<string>(), It.IsAny<VectorStoreCollectionDefinition>()))
            .Returns(this._collectionMock.Object);

        this._collectionMock
            .Setup(c => c.CollectionExistsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        this._collectionMock
            .Setup(c => c.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        this._collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        this._collectionMock
            .Setup(c => c.SearchAsync<string>(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<VectorSearchResult<Dictionary<string, object?>>>());
    }

    [Fact]
    public void ConstructorShouldThrowOnNullArguments()
    {
        // Arrange
        var vectorStore = new Mock<VectorStore>().Object;
        var functions = new List<AIFunction> { CreateFunction("f1") };

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new ContextualFunctionProvider(null!, 1, functions, 3));
        Assert.Throws<ArgumentException>(() => new ContextualFunctionProvider(vectorStore, 0, functions, 3));
        Assert.Throws<ArgumentNullException>(() => new ContextualFunctionProvider(vectorStore, 1, null!, 3));
        Assert.Throws<ArgumentException>(() => new ContextualFunctionProvider(vectorStore, 1, functions, 3, collectionName: ""));
    }

    [Fact]
    public async Task ModelInvokingShouldVectorizeFunctionsOnce()
    {
        // Arrange
        int saveCount = 0;
        var function = CreateFunction("f1", "desc");
        var functions = new List<AIFunction> { function };

        this._collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Callback(() => saveCount++)
            .Returns(Task.CompletedTask);

        var provider = new ContextualFunctionProvider(
            vectorStore: this._vectorStoreMock.Object,
            vectorDimensions: 1536,
            functions: functions,
            maxNumberOfFunctions: 5);

        var messages = new List<ChatMessage> { new() { Contents = [new TextContent("hello")] } };

        // Act
        await provider.ModelInvokingAsync(messages);
        await provider.ModelInvokingAsync(messages);

        // Assert
        Assert.Equal(1, saveCount);
    }

    [Fact]
    public async Task ModelInvokingShouldReturnsRelevantFunctions()
    {
        // Arrange
        var function = CreateFunction("f1", "desc");
        var functions = new List<AIFunction> { function };

        var searchResult = new VectorSearchResult<Dictionary<string, object?>>(
            new Dictionary<string, object?>
            {
                ["Name"] = function.Name,
                ["Description"] = function.Description
            },
            0.99f
        );

        this._collectionMock
            .Setup(c => c.SearchAsync<string>(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(new[] { searchResult }.ToAsyncEnumerable());

        var provider = new ContextualFunctionProvider(
            vectorStore: this._vectorStoreMock.Object,
            vectorDimensions: 1536,
            functions: functions,
            maxNumberOfFunctions: 5);

        var messages = new List<ChatMessage> { new() { Contents = [new TextContent("context")] } };

        // Act
        var result = await provider.ModelInvokingAsync(messages);

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.AIFunctions);
        Assert.Single(result.AIFunctions);
        Assert.Equal("f1", result.AIFunctions[0].Name);
    }

    [Fact]
    public async Task BuildContextShouldUseContextEmbeddingValueProvider()
    {
        // Arrange
        var functions = new List<AIFunction> { CreateFunction("f1") };
        var options = new ContextualFunctionProviderOptions
        {
            ContextEmbeddingValueProvider = (_, _, _) => Task.FromResult("custom context")
        };

        var provider = new ContextualFunctionProvider(
            vectorStore: this._vectorStoreMock.Object,
            vectorDimensions: 1536,
            functions: functions,
            maxNumberOfFunctions: 5,
            options: options);

        var messages = new List<ChatMessage>
        {
            new() { Contents = [new TextContent("ignored")] }
        };

        // Act
        await provider.ModelInvokingAsync(messages);

        // Assert
        this._collectionMock.Verify(
            c => c.SearchAsync<string>("custom context", It.IsAny<int>(), null, It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task BuildContextShouldConcatenatesMessages()
    {
        // Arrange
        var functions = new List<AIFunction> { CreateFunction("f1") };

        var provider = new ContextualFunctionProvider(
            vectorStore: this._vectorStoreMock.Object,
            vectorDimensions: 1536,
            functions: functions,
            maxNumberOfFunctions: 5);

        var message1 = new ChatMessage() { Contents = [new TextContent("msg1")] };
        var message2 = new ChatMessage() { Contents = [new TextContent("msg2")] };
        var message3 = new ChatMessage() { Contents = [new TextContent("msg3")] };

        await provider.MessageAddingAsync(null, message1);
        await provider.MessageAddingAsync(null, message2);
        await provider.MessageAddingAsync(null, message3);

        // Act
        var context = await provider.ModelInvokingAsync([message3]);

        // Assert
        var expected = string.Join(Environment.NewLine, ["msg1", "msg2", "msg3"]);
        this._collectionMock.Verify(c => c.SearchAsync<string>(expected, It.IsAny<int>(), null, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task BuildContextShouldUseEmbeddingValueProvider()
    {
        // Arrange
        List<Dictionary<string, object?>>? upsertedRecords = null;
        this._collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Callback<IEnumerable<Dictionary<string, object?>>, CancellationToken>((records, _) =>
            {
                upsertedRecords = records.ToList();
            })
            .Returns(Task.CompletedTask);

        var functions = new List<AIFunction> { CreateFunction("f1", "desc1") };
        var options = new ContextualFunctionProviderOptions
        {
            EmbeddingValueProvider = (func, ct) => Task.FromResult($"custom embedding for {func.Name}:{func.Description}")
        };

        var provider = new ContextualFunctionProvider(
            vectorStore: this._vectorStoreMock.Object,
            vectorDimensions: 1536,
            functions: functions,
            maxNumberOfFunctions: 5,
            options: options);

        var messages = new List<ChatMessage>
        {
            new() { Contents = [new TextContent("ignored")] }
        };

        // Act
        await provider.ModelInvokingAsync(messages);

        // Assert
        Assert.NotNull(upsertedRecords);
        var embeddingSource = upsertedRecords!.SelectMany(r => r).FirstOrDefault(kv => kv.Key == "Embedding").Value as string;
        Assert.Equal("custom embedding for f1:desc1", embeddingSource);
    }

    [Fact]
    public async Task ContextEmbeddingValueProviderReceivesRecentAndNewMessages()
    {
        // Arrange
        var functions = new List<AIFunction> { CreateFunction("f1") };

        IEnumerable<ChatMessage>? capturedRecentMessages = null;
        IEnumerable<ChatMessage>? capturedNewMessages = null;

        var options = new ContextualFunctionProviderOptions
        {
            NumberOfRecentMessagesInContext = 2,
            ContextEmbeddingValueProvider = (recentMessages, newMessages, ct) =>
            {
                capturedRecentMessages = recentMessages;
                capturedNewMessages = newMessages;

                return Task.FromResult("context");
            }
        };

        var provider = new ContextualFunctionProvider(
            vectorStore: this._vectorStoreMock.Object,
            vectorDimensions: 1536,
            functions: functions,
            maxNumberOfFunctions: 5,
            options: options);

        // Add more messages than the number of messages to keep
        await provider.MessageAddingAsync(null, new() { Contents = [new TextContent("msg1")] });
        await provider.MessageAddingAsync(null, new() { Contents = [new TextContent("msg2")] });
        await provider.MessageAddingAsync(null, new() { Contents = [new TextContent("msg3")] });

        // Act
        await provider.ModelInvokingAsync([
            new() { Contents = [new TextContent("msg4")] },
            new() { Contents = [new TextContent("msg5")] }
        ]);

        // Assert
        Assert.NotNull(capturedRecentMessages);
        Assert.Equal("msg2", capturedRecentMessages.ElementAt(0).Text);
        Assert.Equal("msg3", capturedRecentMessages.ElementAt(1).Text);

        Assert.NotNull(capturedNewMessages);
        Assert.Equal("msg4", capturedNewMessages.ElementAt(0).Text);
        Assert.Equal("msg5", capturedNewMessages.ElementAt(1).Text);
    }

    private static AIFunction CreateFunction(string name, string description = "")
    {
        return AIFunctionFactory.Create(() => { }, name, description);
    }
}
