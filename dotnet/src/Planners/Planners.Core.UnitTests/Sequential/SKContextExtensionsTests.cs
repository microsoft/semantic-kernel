// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planners.UnitTests.XunitHelpers;
using Moq;
using Xunit;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planners.Sequential.UnitTests;
#pragma warning restore IDE0130 // Namespace does not match folder structure

public class SKContextExtensionsTests
{
    [Fact]
    public async Task CanCallGetAvailableFunctionsWithNoFunctionsAsync()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var variables = new ContextVariables();
        var functions = new FunctionCollection();
        var cancellationToken = default(CancellationToken);

        // Arrange Mock Memory and Result
        var memory = new Mock<ISemanticTextMemory>();
        var memoryQueryResult = new MemoryQueryResult(
            new MemoryRecordMetadata(
                isReference: false,
                id: "id",
                text: "text",
                description: "description",
                externalSourceName: "sourceName",
                additionalMetadata: "value"),
            relevance: 0.8,
            embedding: null);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernel.Object, variables, functions);
        var config = new SequentialPlannerConfig() { Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    [Fact]
    public async Task CanCallGetAvailableFunctionsWithFunctionsAsync()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var variables = new ContextVariables();
        var cancellationToken = default(CancellationToken);

        // Arrange FunctionView
        var functionMock = new Mock<ISKFunction>();
        var functionView = new FunctionView("functionName", "pluginName", "description");
        var nativeFunctionView = new FunctionView("nativeFunctionName", "pluginName", "description");
        var functionsView = new List<FunctionView>() { functionView, nativeFunctionView };

        // Arrange Mock Memory and Result
        var functions = new Mock<IFunctionCollection>();
        var memoryQueryResult =
            new MemoryQueryResult(
                new MemoryRecordMetadata(
                    isReference: false,
                    id: functionView.ToFullyQualifiedName(),
                    text: "text",
                    description: "description",
                    externalSourceName: "sourceName",
                    additionalMetadata: "value"),
                relevance: 0.8,
                embedding: null);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        var memory = new Mock<ISemanticTextMemory>();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        functions.Setup(x => x.TryGetFunction(It.IsAny<string>(), It.IsAny<string>(), out It.Ref<ISKFunction?>.IsAny)).Returns(true);
        functions.Setup(x => x.GetFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(functionMock.Object);
        functions.Setup(x => x.GetFunctionViews()).Returns(functionsView);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernel.Object, variables, functions.Object);
        var config = new SequentialPlannerConfig() { Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = (await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count);
        Assert.Equal(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.IncludedFunctions.UnionWith(new List<(string, string)> { ("pluginName", "nativeFunctionName") });

        // Act
        result = (await context.GetAvailableFunctionsAsync(config, semanticQuery)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count); // IncludedFunctions should be added to the result
        Assert.Equal(functionView, result[0]);
        Assert.Equal(nativeFunctionView, result[1]);
    }

    [Fact]
    public async Task CanCallGetAvailableFunctionsWithFunctionsWithRelevancyAsync()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        kernel.SetupGet(k => k.LoggerFactory).Returns(TestConsoleLogger.LoggerFactory);

        var variables = new ContextVariables();
        var cancellationToken = default(CancellationToken);

        // Arrange FunctionView
        var functionMock = new Mock<ISKFunction>();
        var functionView = new FunctionView("functionName", "pluginName", "description");
        var nativeFunctionView = new FunctionView("nativeFunctionName", "pluginName", "description");
        var functionsView = new List<FunctionView>() { functionView, nativeFunctionView };

        // Arrange Mock Memory and Result
        var functions = new Mock<IFunctionCollection>();
        var memoryQueryResult =
            new MemoryQueryResult(
                new MemoryRecordMetadata(
                    isReference: false,
                    id: functionView.ToFullyQualifiedName(),
                    text: "text",
                    description: "description",
                    externalSourceName: "sourceName",
                    additionalMetadata: "value"),
                relevance: 0.8,
                embedding: null);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        var memory = new Mock<ISemanticTextMemory>();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        functions.Setup(x => x.TryGetFunction(It.IsAny<string>(), It.IsAny<string>(), out It.Ref<ISKFunction?>.IsAny)).Returns(true);
        functions.Setup(x => x.GetFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(functionMock.Object);
        functions.Setup(x => x.GetFunctionViews()).Returns(functionsView);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernel.Object, variables, functions.Object);
        var config = new SequentialPlannerConfig { RelevancyThreshold = 0.78, Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = (await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.IncludedFunctions.UnionWith(new List<(string, string)> { ("pluginName", "nativeFunctionName") });

        // Act
        result = (await context.GetAvailableFunctionsAsync(config, semanticQuery)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count); // IncludedFunctions should be added to the result
        Assert.Equal(functionView, result[0]);
        Assert.Equal(nativeFunctionView, result[1]);
    }

    [Fact]
    public async Task CanCallGetAvailableFunctionsAsyncWithDefaultRelevancyAsync()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var variables = new ContextVariables();
        var functions = new FunctionCollection();
        var cancellationToken = default(CancellationToken);

        // Arrange Mock Memory and Result
        var memory = new Mock<ISemanticTextMemory>();
        var memoryQueryResult =
            new MemoryQueryResult(
                new MemoryRecordMetadata(
                    isReference: false,
                    id: "id",
                    text: "text",
                    description: "description",
                    externalSourceName: "sourceName",
                    additionalMetadata: "value"),
                relevance: 0.8,
                embedding: null);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernel.Object, variables, functions);
        var config = new SequentialPlannerConfig { RelevancyThreshold = 0.78, Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
