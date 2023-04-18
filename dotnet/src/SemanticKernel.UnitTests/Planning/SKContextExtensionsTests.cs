// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using SemanticKernel.UnitTests.XunitHelpers;
using Xunit;
using static Microsoft.SemanticKernel.CoreSkills.PlannerSkill;

namespace SemanticKernel.UnitTests.Planning;

public class SKContextExtensionsTests
{
    [Fact]
    public async Task CanCallGetAvailableFunctionsWithNoFunctionsAsync()
    {
        // Arrange
        var variables = new ContextVariables();
        var skills = new SkillCollection();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);

        // Arrange Mock Memory and Result
        var memory = new Mock<ISemanticTextMemory>();
        var memoryQueryResult = new MemoryQueryResult(new MemoryRecordMetadata(false, "sourceName", "id", "description", "text", "value"), 0.8);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(variables, memory.Object, skills.ReadOnlySkillCollection, logger, cancellationToken);
        var config = new PlannerSkillConfig();
        var semanticQuery = "test";

        // Act
        var result = await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true);

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
        var variables = new ContextVariables();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);

        // Arrange FunctionView
        var mockSemanticFunction = new Mock<ISKFunction>();
        var mockNativeFunction = new Mock<ISKFunction>();
        var functionsView = new FunctionsView();
        var functionView = new FunctionView("functionName", "skillName", "description", new List<ParameterView>(), true, false);
        var nativeFunctionView = new FunctionView("nativeFunctionName", "skillName", "description", new List<ParameterView>(), false, false);
        functionsView.AddFunction(functionView);
        functionsView.AddFunction(nativeFunctionView);

        // Arrange Mock Memory and Result
        var skills = new Mock<ISkillCollection>();
        var memoryQueryResult = new MemoryQueryResult(
            new MemoryRecordMetadata(false, "sourceName", functionView.ToFullyQualifiedName(), "description", "text", "value"),
            0.8);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        var memory = new Mock<ISemanticTextMemory>();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        skills.Setup(x => x.HasFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.HasSemanticFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.HasNativeFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.GetSemanticFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(mockSemanticFunction.Object);
        skills.Setup(x => x.GetNativeFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(mockNativeFunction.Object);
        skills.Setup(x => x.GetFunctionsView(It.IsAny<bool>(), It.IsAny<bool>())).Returns(functionsView);
        skills.SetupGet(x => x.ReadOnlySkillCollection).Returns(skills.Object);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = new PlannerSkillConfig();
        var semanticQuery = "test";

        // Act
        var result = (await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count);
        Assert.Equal(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.IncludedFunctions.UnionWith(new List<string> { "nativeFunctionName" });

        // Act
        result = (await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true)).ToList();

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
        var variables = new ContextVariables();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);

        // Arrange FunctionView
        var mockSemanticFunction = new Mock<ISKFunction>();
        var mockNativeFunction = new Mock<ISKFunction>();
        var functionsView = new FunctionsView();
        var functionView = new FunctionView("functionName", "skillName", "description", new List<ParameterView>(), true, false);
        var nativeFunctionView = new FunctionView("nativeFunctionName", "skillName", "description", new List<ParameterView>(), false, false);
        functionsView.AddFunction(functionView);
        functionsView.AddFunction(nativeFunctionView);

        // Arrange Mock Memory and Result
        var skills = new Mock<ISkillCollection>();
        var memoryQueryResult =
            new MemoryQueryResult(
                new MemoryRecordMetadata(isReference: false, id: functionView.ToFullyQualifiedName(), text: "text", description: "description",
                    externalSourceName: "sourceName", additionalMetadata: "value"), relevance: 0.8);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        var memory = new Mock<ISemanticTextMemory>();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        skills.Setup(x => x.HasFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.HasSemanticFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.HasNativeFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.GetSemanticFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(mockSemanticFunction.Object);
        skills.Setup(x => x.GetNativeFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(mockNativeFunction.Object);
        skills.Setup(x => x.GetFunctionsView(It.IsAny<bool>(), It.IsAny<bool>())).Returns(functionsView);
        skills.SetupGet(x => x.ReadOnlySkillCollection).Returns(skills.Object);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = new PlannerSkillConfig() { RelevancyThreshold = 0.78 };
        var semanticQuery = "test";

        // Act
        var result = (await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.IncludedFunctions.UnionWith(new List<string> { "nativeFunctionName" });

        // Act
        result = (await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count); // IncludedFunctions should be added to the result
        Assert.Equal(functionView, result[0]);
        Assert.Equal(nativeFunctionView, result[1]);
    }

    // Tests for GetPlannerSkillConfig
    [Fact]
    public void CanCallGetPlannerSkillConfig()
    {
        // Arrange
        var variables = new ContextVariables();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();
        var expectedDefault = new PlannerSkillConfig();

        // Act
        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = context.GetPlannerSkillConfig();

        // Assert
        Assert.NotNull(config);
        Assert.Equal(expectedDefault.RelevancyThreshold, config.RelevancyThreshold);
        Assert.Equal(expectedDefault.MaxRelevantFunctions, config.MaxRelevantFunctions);
        Assert.Equal(expectedDefault.ExcludedFunctions, config.ExcludedFunctions);
        Assert.Equal(expectedDefault.ExcludedSkills, config.ExcludedSkills);
        Assert.Equal(expectedDefault.IncludedFunctions, config.IncludedFunctions);
    }

    [Fact]
    public void CanCallGetPlannerSkillConfigWithExcludedFunctions()
    {
        // Arrange
        var variables = new ContextVariables();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();
        var expectedDefault = new PlannerSkillConfig();
        var excludedFunctions = "test1,test2,test3";

        // Act
        variables.Set(Parameters.ExcludedFunctions, excludedFunctions);
        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = context.GetPlannerSkillConfig();

        // Assert
        Assert.NotNull(config);
        Assert.Equal(expectedDefault.RelevancyThreshold, config.RelevancyThreshold);
        Assert.Equal(expectedDefault.MaxRelevantFunctions, config.MaxRelevantFunctions);
        Assert.Equal(expectedDefault.ExcludedSkills, config.ExcludedSkills);
        Assert.Equal(expectedDefault.IncludedFunctions, config.IncludedFunctions);
        Assert.Equal(expectedDefault.ExcludedFunctions.Union(new HashSet<string> { "test1", "test2", "test3" }), config.ExcludedFunctions);
    }

    [Fact]
    public void CanCallGetPlannerSkillConfigWithIncludedFunctions()
    {
        // Arrange
        var variables = new ContextVariables();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();
        var expectedDefault = new PlannerSkillConfig();
        var includedFunctions = "test1,CreatePlan";

        // Act
        variables.Set(Parameters.IncludedFunctions, includedFunctions);
        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = context.GetPlannerSkillConfig();

        // Assert
        Assert.NotNull(config);
        Assert.Equal(expectedDefault.RelevancyThreshold, config.RelevancyThreshold);
        Assert.Equal(expectedDefault.MaxRelevantFunctions, config.MaxRelevantFunctions);
        Assert.Equal(expectedDefault.ExcludedSkills, config.ExcludedSkills);
        Assert.Equal(expectedDefault.ExcludedFunctions, config.ExcludedFunctions);
        Assert.Equal(expectedDefault.IncludedFunctions.Union(new HashSet<string> { "test1" }), config.IncludedFunctions);
    }

    [Fact]
    public void CanCallGetPlannerSkillConfigWithRelevancyThreshold()
    {
        // Arrange
        var variables = new ContextVariables();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();
        var expectedDefault = new PlannerSkillConfig();

        // Act
        variables.Set(Parameters.RelevancyThreshold, "0.78");
        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = context.GetPlannerSkillConfig();

        // Assert
        Assert.NotNull(config);
        Assert.Equal(0.78, config.RelevancyThreshold);
        Assert.Equal(expectedDefault.MaxRelevantFunctions, config.MaxRelevantFunctions);
        Assert.Equal(expectedDefault.ExcludedSkills, config.ExcludedSkills);
        Assert.Equal(expectedDefault.ExcludedFunctions, config.ExcludedFunctions);
        Assert.Equal(expectedDefault.IncludedFunctions, config.IncludedFunctions);
    }

    [Fact]
    public void CanCallGetPlannerSkillConfigWithMaxRelevantFunctions()
    {
        // Arrange
        var variables = new ContextVariables();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();
        var expectedDefault = new PlannerSkillConfig();

        // Act
        variables.Set(Parameters.MaxRelevantFunctions, "5");
        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = context.GetPlannerSkillConfig();

        // Assert
        Assert.NotNull(config);
        Assert.Equal(expectedDefault.RelevancyThreshold, config.RelevancyThreshold);
        Assert.Equal(5, config.MaxRelevantFunctions);
        Assert.Equal(expectedDefault.ExcludedSkills, config.ExcludedSkills);
        Assert.Equal(expectedDefault.ExcludedFunctions, config.ExcludedFunctions);
        Assert.Equal(expectedDefault.IncludedFunctions, config.IncludedFunctions);
    }

    [Fact]
    public void CanCallGetPlannerSkillConfigWithExcludedSkills()
    {
        // Arrange
        var variables = new ContextVariables();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();
        var expectedDefault = new PlannerSkillConfig();
        var excludedSkills = "test1,test2,test3";

        // Act
        variables.Set(Parameters.ExcludedSkills, excludedSkills);
        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = context.GetPlannerSkillConfig();

        // Assert
        Assert.NotNull(config);
        Assert.Equal(expectedDefault.RelevancyThreshold, config.RelevancyThreshold);
        Assert.Equal(expectedDefault.MaxRelevantFunctions, config.MaxRelevantFunctions);
        Assert.Equal(expectedDefault.ExcludedFunctions, config.ExcludedFunctions);
        Assert.Equal(expectedDefault.IncludedFunctions, config.IncludedFunctions);
        Assert.Equal(expectedDefault.ExcludedSkills.Union(new HashSet<string> { "test1", "test2", "test3" }), config.ExcludedSkills);
    }

    [Fact]
    public async Task CanCallGetAvailableFunctionsAsyncWithDefaultRelevancyAsync()
    {
        // Arrange
        var variables = new ContextVariables();
        var skills = new SkillCollection();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);

        // Arrange Mock Memory and Result
        var memory = new Mock<ISemanticTextMemory>();
        var memoryQueryResult = new MemoryQueryResult(new MemoryRecordMetadata(false, "sourceName", "id", "description", "text", "value"), 0.8);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(variables, memory.Object, skills.ReadOnlySkillCollection, logger, cancellationToken);
        var config = new PlannerSkillConfig() { RelevancyThreshold = 0.78 };
        var semanticQuery = "test";

        // Act
        var result = await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
