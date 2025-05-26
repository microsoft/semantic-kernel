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
    [Fact]
    public void ConstructorShouldThrowOnNullArguments()
    {
        var vectorStore = new Mock<VectorStore>().Object;
        var functions = new List<AIFunction> { CreateFunction("f1") };

        Assert.Throws<ArgumentNullException>(() => new ContextualFunctionProvider(null!, 1, functions));
        Assert.Throws<ArgumentException>(() => new ContextualFunctionProvider(vectorStore, 0, functions));
        Assert.Throws<ArgumentNullException>(() => new ContextualFunctionProvider(vectorStore, 1, null!));
        Assert.Throws<ArgumentException>(() => new ContextualFunctionProvider(vectorStore, 1, functions, collectionName: ""));
    }

    [Fact]
    public async Task ModelInvokingShouldVectorizeFunctionsOnce()
    {
        // Arrange
        var vectorStoreMock = new Mock<VectorStore>(MockBehavior.Strict);

        // Setup the vector store to return a mock collection
        var collectionMock = new Mock<VectorStoreCollection<object, Dictionary<string, object?>>>(MockBehavior.Strict);
        vectorStoreMock
            .Setup(vs => vs.GetDynamicCollection(It.IsAny<string>(), It.IsAny<VectorStoreCollectionDefinition>()))
            .Returns(collectionMock.Object);

        // Setup collection existence
        collectionMock
            .Setup(c => c.CollectionExistsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Setup SaveAsync and SearchAsync on FunctionStore
        int saveCount = 0;
        var function = CreateFunction("f1", "desc");
        var functions = new List<AIFunction> { function };

        // We need to track SaveAsync and SearchAsync, so we use a custom FunctionStoreOptions
        var options = new ContextualFunctionProviderOptions
        {
            MaxNumberOfFunctions = 1
        };

        // Use the real ContextualFunctionProvider, which will create a real FunctionStore
        var provider = new ContextualFunctionProvider(vectorStoreMock.Object, 3, functions, options);

        // Patch the SaveAsync and SearchAsync methods on the collection to simulate FunctionStore behavior
        collectionMock
            .Setup(c => c.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Callback(() => saveCount++)
            .Returns(Task.CompletedTask);

        collectionMock
            .Setup(c => c.SearchAsync<string>(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<VectorSearchResult<Dictionary<string, object?>>>());

        // Act
        var messages = new List<ChatMessage> { new() { Contents = [new TextContent("hello")] } };
        await provider.ModelInvokingAsync(messages);
        await provider.ModelInvokingAsync(messages);

        // Assert
        Assert.Equal(1, saveCount); // UpsertAsync (SaveAsync) should be called only once
    }

    [Fact]
    public async Task ModelInvokingShouldReturnsRelevantFunctions()
    {
        // Arrange
        var vectorStoreMock = new Mock<VectorStore>(MockBehavior.Strict);

        // Setup the vector store to return a mock collection
        var collectionMock = new Mock<VectorStoreCollection<object, Dictionary<string, object?>>>(MockBehavior.Strict);
        vectorStoreMock
            .Setup(vs => vs.GetDynamicCollection(It.IsAny<string>(), It.IsAny<VectorStoreCollectionDefinition>()))
            .Returns(collectionMock.Object);

        // Setup collection existence
        collectionMock
            .Setup(c => c.CollectionExistsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        collectionMock
            .Setup(c => c.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        // Setup UpsertAsync to simulate SaveAsync
        collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        // Setup SearchAsync to return a function as a search result
        var function = CreateFunction("f1", "desc");
        var functions = new List<AIFunction> { function };

        // Simulate a vector search result that would map to our function
        var searchResult = new VectorSearchResult<Dictionary<string, object?>>(
            new Dictionary<string, object?>
            {
                ["Name"] = function.Name,
                ["Description"] = function.Description
            },
            0.99f
        );

        collectionMock
            .Setup(c => c.SearchAsync<string>(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(new[] { searchResult }.ToAsyncEnumerable());

        var options = new ContextualFunctionProviderOptions
        {
            MaxNumberOfFunctions = 1
        };

        var provider = new ContextualFunctionProvider(vectorStoreMock.Object, 3, functions, options);

        // Act
        var messages = new List<ChatMessage> { new() { Contents = [new TextContent("context")] } };
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
        var vectorStoreMock = new Mock<VectorStore>(MockBehavior.Strict);

        // Setup the vector store to return a mock collection
        var collectionMock = new Mock<VectorStoreCollection<object, Dictionary<string, object?>>>(MockBehavior.Strict);
        vectorStoreMock
            .Setup(vs => vs.GetDynamicCollection(It.IsAny<string>(), It.IsAny<VectorStoreCollectionDefinition>()))
            .Returns(collectionMock.Object);

        // Setup collection existence
        collectionMock
            .Setup(c => c.CollectionExistsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        collectionMock
            .Setup(c => c.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        collectionMock
            .Setup(c => c.SearchAsync<string>(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<VectorSearchResult<Dictionary<string, object?>>>());

        var functions = new List<AIFunction> { CreateFunction("f1") };
        var options = new ContextualFunctionProviderOptions
        {
            ContextEmbeddingValueProvider = (_, ct) => Task.FromResult("custom context")
        };

        var provider = new ContextualFunctionProvider(vectorStoreMock.Object, 3, functions, options);

        var messages = new List<ChatMessage>
        {
            new() { Contents = [new TextContent("ignored")] }
        };

        // Act
        await provider.ModelInvokingAsync(messages);

        // Assert
        collectionMock.Verify(
            c => c.SearchAsync<string>("custom context", It.IsAny<int>(), null, It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task BuildContextShouldConcatenatesMessages()
    {
        // Arrange
        var vectorStoreMock = new Mock<VectorStore>(MockBehavior.Strict);

        // Setup the vector store to return a mock collection
        var collectionMock = new Mock<VectorStoreCollection<object, Dictionary<string, object?>>>(MockBehavior.Strict);
        vectorStoreMock
            .Setup(vs => vs.GetDynamicCollection(It.IsAny<string>(), It.IsAny<VectorStoreCollectionDefinition>()))
            .Returns(collectionMock.Object);

        // Setup collection existence
        collectionMock
            .Setup(c => c.CollectionExistsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        collectionMock
            .Setup(c => c.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        collectionMock
            .Setup(c => c.SearchAsync<string>(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<VectorSearchResult<Dictionary<string, object?>>>());

        var functions = new List<AIFunction> { CreateFunction("f1") };
        var provider = new ContextualFunctionProvider(vectorStoreMock.Object, 3, functions);

        var messages = new List<ChatMessage>
        {
            new() { Contents = [new TextContent("msg1")] },
            new() { Contents = [new TextContent("msg2")] },
            new() { Contents = [new TextContent("")] },
            new() { Contents = null }
        };

        // Act
        var context = await provider.ModelInvokingAsync(messages);

        // Assert
        var expected = "msg1" + Environment.NewLine + "msg2";
        collectionMock.Verify(c => c.SearchAsync<string>(expected, It.IsAny<int>(), null, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task BuildContextShouldUseEmbeddingValueProvider()
    {
        // Arrange
        var vectorStoreMock = new Mock<VectorStore>(MockBehavior.Strict);

        // Setup the vector store to return a mock collection
        var collectionMock = new Mock<VectorStoreCollection<object, Dictionary<string, object?>>>(MockBehavior.Strict);
        vectorStoreMock
            .Setup(vs => vs.GetDynamicCollection(It.IsAny<string>(), It.IsAny<VectorStoreCollectionDefinition>()))
            .Returns(collectionMock.Object);

        // Setup collection existence
        collectionMock
            .Setup(c => c.CollectionExistsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        collectionMock
            .Setup(c => c.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        // We'll capture the upserted records to verify the embedding value
        List<Dictionary<string, object?>>? upsertedRecords = null;
        collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Callback<IEnumerable<Dictionary<string, object?>>, CancellationToken>((records, _) =>
            {
                upsertedRecords = records.ToList();
            })
            .Returns(Task.CompletedTask);

        collectionMock
            .Setup(c => c.SearchAsync<string>(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<VectorSearchResult<Dictionary<string, object?>>>());

        var functions = new List<AIFunction> { CreateFunction("f1", "desc1") };
        var options = new ContextualFunctionProviderOptions
        {
            EmbeddingValueProvider = (func, ct) => Task.FromResult($"custom embedding for {func.Name}:{func.Description}")
        };

        var provider = new ContextualFunctionProvider(vectorStoreMock.Object, 3, functions, options);

        var messages = new List<ChatMessage>
        {
            new() { Contents = [new TextContent("ignored")] }
        };

        // Act
        await provider.ModelInvokingAsync(messages);

        // Assert
        Assert.NotNull(upsertedRecords);

        // The embedding value should be present in the upserted record(s)
        var embeddingSource = upsertedRecords!.SelectMany(r => r).FirstOrDefault(kv => kv.Key == "Embedding").Value as string;
        Assert.Equal("custom embedding for f1:desc1", embeddingSource);
    }


    private static AIFunction CreateFunction(string name, string description = "")
    {
        return AIFunctionFactory.Create(() => { }, name, description);
    }
}
