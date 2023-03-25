// Copyright (c) Microsoft. All rights reserved.

using System;
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
    [InlineData("", ConditionalSkill.NoReasonMessage)]
    [InlineData("Unexpected Result", ConditionalSkill.NoReasonMessage)]
    [InlineData("ERROR", ConditionalSkill.NoReasonMessage)]
    [InlineData("ERROR REASON: Something1 Error", "Something1 Error")]
    [InlineData("ERROR\nReason:Something2 Error", "Something2 Error")]
    [InlineData("ERROR\n\n Reason:\nSomething3 Error", "Something3 Error")]
    [InlineData("FALSE", ConditionalSkill.NoReasonMessage)]
    [InlineData("FALSE reason: Something1 False", "Something1 False")]
    [InlineData("FALSE\nReason:Something2 False", "Something2 False")]
    [InlineData("FALSE\n\n Reason:\nSomething3 False", "Something3 False")]
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
                .ReturnsAsync("TRUE");

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
                .ReturnsAsync("TRUE");

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
                .ReturnsAsync("TRUE");

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
