// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.ControlFlow;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests.CoreSkills;

public class ConditionalSkillTests
{
    private readonly ITestOutputHelper _testOutputHelper;

    private const string GoalText = "Solve the equation x^2 = 2.";

    public ConditionalSkillTests(ITestOutputHelper testOutputHelper)
    {
        this._testOutputHelper = testOutputHelper;
        this._testOutputHelper.WriteLine("Tests initialized");
    }

    [Fact]
    public void ItCanBeInstantiated()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");

        // Act - Assert no exception occurs
        _ = new ConditionalSkill(kernel);
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");

        // Act - Assert no exception occurs e.g. due to reflection
        _ = kernel.ImportSkill(new ConditionalSkill(kernel), "condition");
    }

    [Fact]
    public async Task ItCanRunIfAsync()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletionClient>();
        var conditionalSkill = new ConditionalSkill(kernel, completionBackendMock.Object);
        var condition = kernel.ImportSkill(conditionalSkill, "conditional");

        // Act
        var context = await kernel.RunAsync(GoalText, condition["IfAsync"]);

        // Assert
        Assert.NotNull(context);
    }

    [Theory]
    [InlineData("")]
    [InlineData("Unexpected Result")]
    public async Task InvalidJsonIfStatementCheckResponseShouldFailContextAsync(string llmResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletionClient>();
        completionBackendMock.Setup(a => a.CompleteAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(llmResult);
        var conditionalSkill = new ConditionalSkill(kernel, completionBackendMock.Object);
        var functions = kernel.ImportSkill(conditionalSkill, "conditional");

        // Act
        var context = await kernel.RunAsync("Any", functions["IfAsync"]);

        // Assert
        Assert.NotNull(context);
        Assert.True(context.ErrorOccurred);
        Assert.NotNull(context.LastException);
        Assert.IsType<ConditionException>(context.LastException);
        Assert.Equal(ConditionException.ErrorCodes.JsonResponseNotFound, ((ConditionException)context.LastException).ErrorCode);
    }

    [Theory]
    [InlineData("{\"valid\": false, \"reason\": null}", ConditionalSkill.NoReasonMessage)]
    [InlineData("{\"valid\": false, \"reason\": \"Something1 Error\"}", "Something1 Error")]
    [InlineData("{\"valid\": false, \n\"reason\": \"Something2 Error\"}", "Something2 Error")]
    [InlineData("{\"valid\": false, \n\n\"reason\": \"Something3 Error\"}", "Something3 Error")]
    public async Task InvalidIfStatementCheckResponseShouldFailContextWithReasonMessageAsync(string llmResult, string expectedReason)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletionClient>();
        completionBackendMock.Setup(a => a.CompleteAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(llmResult);
        var conditionalSkill = new ConditionalSkill(kernel, completionBackendMock.Object);
        var functions = kernel.ImportSkill(conditionalSkill, "conditional");

        // Act
        var context = await kernel.RunAsync("Any", functions["IfAsync"]);

        // Assert
        Assert.NotNull(context);
        Assert.True(context.ErrorOccurred);
        Assert.NotNull(context.LastException);
        Assert.IsType<ConditionException>(context.LastException);
        Assert.Equal(ConditionException.ErrorCodes.InvalidStatementStructure, ((ConditionException)context.LastException).ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.InvalidStatementStructure)}: {expectedReason}", ((ConditionException)context.LastException).Message);
    }

    [Theory]
    [InlineData("", ConditionalSkill.NoReasonMessage)]
    [InlineData("Unexpected Result", ConditionalSkill.NoReasonMessage)]
    [InlineData("ERROR", ConditionalSkill.NoReasonMessage)]
    [InlineData("ERROR reason: Something1 Error", "Something1 Error")]
    [InlineData("ERROR\nREASON:Something2 Error", "Something2 Error")]
    [InlineData("ERROR\n\n ReAson:\nSomething3 Error", "Something3 Error")]
    public async Task InvalidEvaluateConditionResponseShouldFailContextWithReasonMessageAsync(string llmResult, string expectedReason)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletionClient>();
        var ifContent = "Any";
        var ifCheckPrompt = ConditionalSkill.IfStructureCheckPrompt[..30];
        var evalConditionPrompt = ConditionalSkill.EvaluateConditionPrompt[..30];

        // To be able to check the condition need ensure success in the if statement check first
        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(ifCheckPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync("{\"valid\": true}");

        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(evalConditionPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync(llmResult);

        var conditionalSkill = new ConditionalSkill(kernel, completionBackendMock.Object);
        var functions = kernel.ImportSkill(conditionalSkill, "conditional");

        // Act
        var context = await kernel.RunAsync(ifContent, functions["IfAsync"]);

        // Assert
        Assert.NotNull(context);
        Assert.True(context.ErrorOccurred);
        Assert.NotNull(context.LastException);
        Assert.IsType<ConditionException>(context.LastException);
        Assert.Equal(ConditionException.ErrorCodes.InvalidConditionFormat, ((ConditionException)context.LastException).ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.InvalidConditionFormat)}: {expectedReason}", ((ConditionException)context.LastException).Message);
    }

    [Theory]
    [InlineData("TRUE", "Then")]
    [InlineData("True", "Then")]
    [InlineData("true", "Then")]
    [InlineData("FALSE", "Else")]
    [InlineData("False", "Else")]
    [InlineData("false", "Else")]
    public async Task ValidEvaluateConditionResponseShouldReturnAsync(string llmResult, string expectedBranchTag)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletionClient>();
        var ifContent = "Any";
        var ifCheckPrompt = ConditionalSkill.IfStructureCheckPrompt[..30];
        var evalConditionPrompt = ConditionalSkill.EvaluateConditionPrompt[..30];

        // To be able to check the condition need ensure success in the if statement check first
        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(ifCheckPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync($"{{\"valid\": true}}");

        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(evalConditionPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync(llmResult);

        var conditionalSkill = new ConditionalSkill(kernel, completionBackendMock.Object);
        var functions = kernel.ImportSkill(conditionalSkill, "conditional");

        // Act
        var context = await kernel.RunAsync(ifContent, functions["IfAsync"]);

        // Assert
        Assert.NotNull(context);
        Assert.True(context.Variables.ContainsKey("EvaluateIfBranchTag"));
        Assert.Equal(expectedBranchTag, context["EvaluateIfBranchTag"]);
    }

    [Theory]
    [InlineData("Variable1,Variable2", "Variable1")]
    [InlineData("Variable1,Variable2", "")]
    [InlineData("Variable1,Variable2,Variable3", "Variable2")]
    public async Task EvaluateShouldUseExistingConditionVariablesOnlyAsync(string existingVariables, string conditionVariables)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletionClient>();
        var ifContent = "Any";
        var ifCheckPrompt = ConditionalSkill.IfStructureCheckPrompt[..30];
        var evalConditionPrompt = ConditionalSkill.EvaluateConditionPrompt[..30];

        // To be able to check the condition need ensure success in the if statement check first
        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(ifCheckPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync($"{{\"valid\": true, \"variables\": [\"{string.Join("\",\"", conditionVariables.Split(','))}\"]}}");

        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(evalConditionPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync("TRUE");

        var conditionalSkill = new ConditionalSkill(kernel, completionBackendMock.Object);
        var functions = kernel.ImportSkill(conditionalSkill, "conditional");

        var contextVariables = new ContextVariables(ifContent);
        if (!string.IsNullOrEmpty(existingVariables))
        {
            foreach (var variableName in existingVariables.Split(','))
            {
                contextVariables.Set(variableName, "x");
            }
        }
        IEnumerable<string> notExpectedVariablesInPrompt = existingVariables.Split(',');
        if (!string.IsNullOrEmpty(conditionVariables))
        {
            notExpectedVariablesInPrompt = notExpectedVariablesInPrompt.Except(conditionVariables.Split(','));
        }

        // Act
        var context = await kernel.RunAsync(contextVariables, functions["IfAsync"]);

        // Assert
        Assert.NotNull(context);
        Assert.True(context.Variables.ContainsKey("ConditionalVariables"));
        if (!string.IsNullOrEmpty(conditionVariables))
        {
            foreach (var variableName in conditionVariables.Split(','))
            {
                Assert.Contains(variableName, context.Variables["ConditionalVariables"], StringComparison.InvariantCulture);
            }
        }

        foreach (var variableName in notExpectedVariablesInPrompt)
        {
            Assert.DoesNotContain(variableName, context.Variables["ConditionalVariables"], StringComparison.InvariantCulture);
        }
    }

    [Theory]
    [InlineData("Variable1,Variable2", "Variable4")]
    [InlineData("Variable1,Variable2,Variable3", "Variable5,Variable2")]
    public async Task InvalidEvaluateWhenConditionVariablesDontExistsAsync(string existingVariables, string conditionVariables)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletionClient>();
        var ifContent = "Any";
        var ifCheckPrompt = ConditionalSkill.IfStructureCheckPrompt[..30];
        var evalConditionPrompt = ConditionalSkill.EvaluateConditionPrompt[..30];

        // To be able to check the condition need ensure success in the if statement check first
        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(ifCheckPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync($"{{\"valid\": true, \"variables\": [\"{string.Join("\",\"", conditionVariables.Split(','))}\"]}}");

        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(evalConditionPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync("TRUE");

        var conditionalSkill = new ConditionalSkill(kernel, completionBackendMock.Object);
        var functions = kernel.ImportSkill(conditionalSkill, "conditional");

        var contextVariables = new ContextVariables(ifContent);
        if (!string.IsNullOrEmpty(existingVariables))
        {
            foreach (var variableName in existingVariables.Split(','))
            {
                contextVariables.Set(variableName, "x");
            }
        }
        IEnumerable<string> expectedNotFound = Enumerable.Empty<string>();
        if (!string.IsNullOrEmpty(conditionVariables))
        {
            expectedNotFound = conditionVariables.Split(',').Except(existingVariables?.Split(",") ?? Array.Empty<string>());
        }

        // Act
        var context = await kernel.RunAsync(contextVariables, functions["IfAsync"]);

        // Assert
        Assert.True(context.ErrorOccurred);
        Assert.NotNull(context.LastException);
        Assert.IsType<ConditionException>(context.LastException);
        Assert.Equal(ConditionException.ErrorCodes.ContextVariablesNotFound, ((ConditionException)context.LastException).ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.ContextVariablesNotFound)}: {string.Join(", ", expectedNotFound)}", ((ConditionException)context.LastException).Message);
    }

    [Theory]
    [InlineData("")]
    [InlineData("Result1")]
    public async Task ValidIfShouldReturnGetThenOrElseBranchResponseAsync(string thenOrElseLLMResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletionClient>();
        var ifContent = "Any";
        var ifCheckPrompt = ConditionalSkill.IfStructureCheckPrompt[..30];
        var evalConditionPrompt = ConditionalSkill.EvaluateConditionPrompt[..30];
        var extractThenOrElseFromIfPrompt = ConditionalSkill.ExtractThenOrElseFromIfPrompt[..30];

        // To be able to check the condition need ensure success in the if statement check first
        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(ifCheckPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync("{\"valid\": true}");

        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(evalConditionPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync("TRUE");

        completionBackendMock.Setup(a =>
            a.CompleteAsync(It.Is<string>(prompt => prompt.Contains(extractThenOrElseFromIfPrompt)), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync(thenOrElseLLMResult);

        var conditionalSkill = new ConditionalSkill(kernel, completionBackendMock.Object);
        var functions = kernel.ImportSkill(conditionalSkill, "conditional");

        // Act
        var context = await kernel.RunAsync(ifContent, functions["IfAsync"]);

        // Assert
        Assert.NotNull(context);
        Assert.False(context.ErrorOccurred);
        Assert.Equal(thenOrElseLLMResult, context.ToString());
    }
}
