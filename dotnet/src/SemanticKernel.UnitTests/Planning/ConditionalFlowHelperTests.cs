// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Moq;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests.Planning;

public class ConditionalFlowHelperTests
{
    private readonly ITestOutputHelper _testOutputHelper;

    public ConditionalFlowHelperTests(ITestOutputHelper testOutputHelper)
    {
        this._testOutputHelper = testOutputHelper;
        this._testOutputHelper.WriteLine("Tests initialized");
    }

    [Fact]
    public void ItCanBeInstantiated()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var completionBackendMock = new Mock<ITextCompletion>();

        // Act - Assert no exception occurs
        _ = new ConditionalFlowHelper(kernel);
        _ = new ConditionalFlowHelper(kernel, completionBackendMock.Object);
    }

    [Fact]
    public async Task ItCanRunIfAsync()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], "TRUE" },
            { ConditionalFlowHelper.ExtractThenOrElseFromIfPrompt[..30], "Something" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var context = await target.IfAsync("<if><conditiongroup/></if>", this.CreateSKContext(kernel));

        // Assert
        Assert.NotNull(context);
        Assert.Equal("Something", context.ToString());
    }

    [Theory]
    [InlineData("")]
    [InlineData("Unexpected Result")]
    public async Task InvalidJsonIfStatementCheckResponseShouldFailContextAsync(string llmResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], llmResult }
        });
        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync("Any", this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.JsonResponseNotFound, exception.ErrorCode);
    }

    [Fact]
    public async Task InvalidIfStatementWithoutConditionShouldFailAsync()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");

        // To be able to check the condition need ensure success in the if statement check first
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync("Any", this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidConditionFormat, exception.ErrorCode);
    }

    [Theory]
    [InlineData("{\"valid\": false, \"reason\": null}", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("{\"valid\": false, \"reason\": \"Something1 Error\"}", "Something1 Error")]
    [InlineData("{\"valid\": false, \n\"reason\": \"Something2 Error\"}", "Something2 Error")]
    [InlineData("{\"valid\": false, \n\n\"reason\": \"Something3 Error\"}", "Something3 Error")]
    public async Task InvalidIfStatementCheckResponseShouldFailContextWithReasonMessageAsync(string llmResult, string expectedReason)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], llmResult },
        });
        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync("Any", this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidStatementStructure, exception.ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.InvalidStatementStructure)}: {expectedReason}", exception.Message);
    }

    [Theory]
    [InlineData("", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("Unexpected Result", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("ERROR", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("ERROR reason: Something1 Error", "Something1 Error")]
    [InlineData("ERROR\nREASON:Something2 Error", "Something2 Error")]
    [InlineData("ERROR\n\n ReAson:\nSomething3 Error", "Something3 Error")]
    public async Task InvalidEvaluateConditionResponseShouldFailContextWithReasonMessageAsync(string llmResult, string expectedReason)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var ifContent = "<if><conditiongroup/></if>";
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], llmResult },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync(ifContent, this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidConditionFormat, exception.ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.InvalidConditionFormat)}: {expectedReason}", exception.Message);
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
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var ifContent = "<if><conditiongroup></conditiongroup><then></then></if>";
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], llmResult },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var context = await target.IfAsync(ifContent, this.CreateSKContext(kernel));

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
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var ifContent = "<if><conditiongroup></conditiongroup><then></then></if>";
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            {
                ConditionalFlowHelper.IfStructureCheckPrompt[..30],
                $"{{\"valid\": true, \"variables\": [\"{string.Join("\",\"", conditionVariables.Split(','))}\"]}}"
            },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], "TRUE" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

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
        var context = await target.IfAsync(ifContent, this.CreateSKContext(kernel, contextVariables));

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
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var ifContent = "<if><conditiongroup></conditiongroup><then></then></if>";
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], $"{{\"valid\": true, \"variables\": [\"{string.Join("\",\"", conditionVariables.Split(','))}\"]}}" },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], "TRUE" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

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
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync("<if><conditiongroup/></if>", this.CreateSKContext(kernel, contextVariables));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.ContextVariablesNotFound, exception.ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.ContextVariablesNotFound)}: {string.Join(", ", expectedNotFound)}", exception.Message);
    }

    [Theory]
    [InlineData("")]
    [InlineData("Result1")]
    public async Task ValidIfShouldReturnGetThenOrElseBranchResponseAsync(string thenOrElseLlmResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletion("test", "test", "test");
        var ifContent = "<if><conditiongroup></conditiongroup><then></then></if>";
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{ \"valid\": true }" },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], "TRUE" },
            { ConditionalFlowHelper.ExtractThenOrElseFromIfPrompt[..30], thenOrElseLlmResult }
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);
        // Act
        var context = await target.IfAsync(ifContent, this.CreateSKContext(kernel));

        // Assert
        Assert.NotNull(context);
        Assert.False(context.ErrorOccurred);
        Assert.Equal(thenOrElseLlmResult, context.ToString());
    }

    private SKContext CreateSKContext(IKernel kernel, ContextVariables? variables = null, CancellationToken cancellationToken = default)
    {
        return new SKContext(variables ?? new ContextVariables(), kernel.Memory, kernel.Skills, kernel.Log, cancellationToken);
    }

    private static Mock<ITextCompletion> SetupCompletionBackendMock(Dictionary<string, string> promptsAndResponses)
    {
        var completionBackendMock = new Mock<ITextCompletion>();

        // For each prompt and response pair, setup the mock to return the response when the prompt is passed as an argument
        foreach (var pair in promptsAndResponses)
        {
            completionBackendMock.Setup(a => a.CompleteAsync(
                It.Is<string>(prompt => prompt.Contains(pair.Key)), // Match the prompt by checking if it contains the expected substring
                It.IsAny<CompleteRequestSettings>(), // Ignore the settings parameter
                It.IsAny<CancellationToken>() // Ignore the cancellation token parameter
            )).ReturnsAsync(pair.Value); // Return the expected response
        }

        return completionBackendMock;
    }
}
