// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Sequential;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using SemanticKernel.Extensions.UnitTests.XunitHelpers;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Planning.SequentialPlanner;

public class SKContextExtensionsTests
{
    private async IAsyncEnumerable<T> GetAsyncEnumerableAsync<T>(IEnumerable<T> results)
    {
        foreach (T result in results)
        {
            yield return await Task.FromResult(result);
        }
    }

    [Fact]
    public async Task CanCallGetAvailableFunctionsWithNoFunctionsAsync()
    {
        // Arrange
        var kernel = new Mock<IKernel>();

        var variables = new ContextVariables();
        var skills = new SkillCollection();
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
        IAsyncEnumerable<MemoryQueryResult> asyncEnumerable = this.GetAsyncEnumerableAsync(new[] { memoryQueryResult });
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        var kernelContext = new Mock<IKernelExecutionContext>();
        kernelContext.SetupGet(x => x.Skills).Returns(skills);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernelContext.Object, variables);
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
        var functionView = new FunctionView("functionName", "skillName", "description");
        var nativeFunctionView = new FunctionView("nativeFunctionName", "skillName", "description");
        var functionsView = new List<FunctionView>() { functionView, nativeFunctionView };

        // Arrange Mock Memory and Result
        var skills = new Mock<ISkillCollection>();
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
        var asyncEnumerable = this.GetAsyncEnumerableAsync(new[] { memoryQueryResult });
        var memory = new Mock<ISemanticTextMemory>();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        skills.Setup(x => x.TryGetFunction(It.IsAny<string>(), It.IsAny<string>(), out It.Ref<ISKFunction?>.IsAny)).Returns(true);
        skills.Setup(x => x.GetFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(functionMock.Object);
        skills.Setup(x => x.GetFunctionViews()).Returns(functionsView);

        var kernelContext = new Mock<IKernelExecutionContext>();
        kernelContext.SetupGet(x => x.Skills).Returns(skills.Object);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernelContext.Object, variables);
        var config = new SequentialPlannerConfig() { Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = (await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count);
        Assert.Equal(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.IncludedFunctions.UnionWith(new List<string> { "nativeFunctionName" });

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

        var variables = new ContextVariables();
        var cancellationToken = default(CancellationToken);

        // Arrange FunctionView
        var functionMock = new Mock<ISKFunction>();
        var functionView = new FunctionView("functionName", "skillName", "description");
        var nativeFunctionView = new FunctionView("nativeFunctionName", "skillName", "description");
        var functionsView = new List<FunctionView>() { functionView, nativeFunctionView };

        // Arrange Mock Memory and Result
        var skills = new Mock<ISkillCollection>();
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
        var asyncEnumerable = this.GetAsyncEnumerableAsync(new[] { memoryQueryResult });
        var memory = new Mock<ISemanticTextMemory>();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        skills.Setup(x => x.TryGetFunction(It.IsAny<string>(), It.IsAny<string>(), out It.Ref<ISKFunction?>.IsAny)).Returns(true);
        skills.Setup(x => x.GetFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(functionMock.Object);
        skills.Setup(x => x.GetFunctionViews()).Returns(functionsView);

        var kernelContext = new Mock<IKernelExecutionContext>();
        kernelContext.SetupGet(k => k.LoggerFactory).Returns(TestConsoleLogger.LoggerFactory);
        kernelContext.SetupGet(x => x.Skills).Returns(skills.Object);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernelContext.Object, variables);
        var config = new SequentialPlannerConfig { RelevancyThreshold = 0.78, Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = (await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.IncludedFunctions.UnionWith(new List<string> { "nativeFunctionName" });

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
        var kernelContext = new Mock<IKernelExecutionContext>();

        var variables = new ContextVariables();
        var skills = new SkillCollection();
        var cancellationToken = default(CancellationToken);

        kernelContext.SetupGet(x => x.Skills).Returns(skills);

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
        var asyncEnumerable = this.GetAsyncEnumerableAsync(new[] { memoryQueryResult });
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernelContext.Object, variables);
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
