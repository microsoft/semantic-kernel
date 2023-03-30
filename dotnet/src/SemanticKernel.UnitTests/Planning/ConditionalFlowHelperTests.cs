// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Xml;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Moq;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests.Planning;

public class ConditionalFlowHelperTests
{
    private readonly ITestOutputHelper _testOutputHelper;
    private const string ValidIfStructure = "<if condition=\"a equals 0\"><function/></if>";

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
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
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
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], "{\"valid\": true, \"condition\": true}" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var resultingBranch = await target.IfAsync(ValidIfStructure, this.CreateSKContext(kernel));

        // Assert
        Assert.NotNull(resultingBranch);
        Assert.Equal("<function />", resultingBranch);
    }

    [Theory]
    [InlineData("{\"valid\": true}")]
    [InlineData("{\"valid\": true, \"condition\": null}")]
    public async Task InvalidConditionJsonPropertyShouldFailAsync(string llmConditionResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], llmConditionResult },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync(ValidIfStructure, this.CreateSKContext(kernel));
        });

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(ConditionException.ErrorCodes.InvalidResponse, exception.ErrorCode);
    }

    [Fact]
    public async Task InvalidIfStatementWithoutConditionShouldFailAsync()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");

        // To be able to check the condition need ensure success in the if statement check first
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync("<if></if>", this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidCondition, exception.ErrorCode);
    }

    [Theory]
    [InlineData("")]
    [InlineData("Unexpected Result")]
    public async Task InvalidJsonIfStatementCheckResponseShouldFailContextAsync(string llmResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], llmResult }
        });
        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync(ValidIfStructure, this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidResponse, exception.ErrorCode);
    }

    [Theory]
    [InlineData("TRUE<else>")]
    [InlineData("<if condition=\"a contains b\">")]
    [InlineData("<i f condition=\"a contains b\">")]
    [InlineData("<else condition=\"a contains b\">")]
    [InlineData("<if condition=\"a contains b\"><else></if>")]
    [InlineData("</if>")]
    public async Task InvalidIfStatementWithoutClosingTagsShouldFailAsync(string ifContentInput)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");

        // To be able to check the condition need ensure success in the if statement check first
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<XmlException>(async () =>
        {
            await target.IfAsync(ifContentInput, this.CreateSKContext(kernel));
        });

        // Assert
        Assert.NotNull(exception);
    }

    [Theory]
    [InlineData("{\"valid\": false, \"reason\": null}", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("{\"valid\": false, \"reason\": \"\"}", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("{\"valid\": false, \"reason\": \"Something1 Error\"}", "Something1 Error")]
    [InlineData("{\"valid\": false, \n\"reason\": \"Something2 Error\"}", "Something2 Error")]
    [InlineData("{\"valid\": false, \n\n\"reason\": \"Something3 Error\"}", "Something3 Error")]
    public async Task InvalidIfStatementCheckResponseShouldFailContextWithReasonMessageAsync(string llmResult, string expectedReason)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], llmResult },
        });
        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync(ValidIfStructure, this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidStatementStructure, exception.ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.InvalidStatementStructure)}: {expectedReason}", exception.Message);
    }

    [Theory]
    [InlineData("{\"valid\": false }", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("{\"valid\": false \n}", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("{\"valid\": false, \n \"reason\":\"\" }", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("{\"valid\": false, \n\n\"reason\": \"Something1 Error\"}", "Something1 Error")]
    [InlineData("{\"valid\": false, \n\n\"reason\": \"Something2 Error\"}", "Something2 Error")]
    [InlineData("{\"valid\": false, \n\n\"reason\": \"Something3 Error\"}", "Something3 Error")]
    public async Task InvalidEvaluateConditionResponseShouldFailContextWithReasonMessageAsync(string llmResult, string expectedReason)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var ifContent = ValidIfStructure;
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
        Assert.Equal(ConditionException.ErrorCodes.InvalidCondition, exception.ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.InvalidCondition)}: {expectedReason}", exception.Message);
    }

    [Theory]
    [InlineData("{\"valid\": true, \"condition\": true}", "<if condition=\"a equals 0\"><functionIf/></if>", "<functionIf />")]
    [InlineData("{\"valid\": true, \"condition\": false}", "<if condition=\"a equals 0\"><functionIf/></if>", "")]
    [InlineData("{\"valid\": true, \"condition\": true}", "<if condition=\"a equals 0\"><functionIf/></if><else><functionElse/></else>", "<functionIf />")]
    [InlineData("{\"valid\": true, \"condition\": false}", "<if condition=\"a equals 0\"><functionIf/></if><else><functionElse/></else>", "<functionElse />")]
    public async Task ValidEvaluateConditionResponseShouldReturnAsync(string llmResult, string inputIfStructure, string expectedResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowHelper.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], llmResult },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var result = await target.IfAsync(inputIfStructure, this.CreateSKContext(kernel));

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedResult, result);
    }

    [Theory]
    [InlineData("Variable1,Variable2", "Variable1")]
    [InlineData("Variable1,Variable2", "")]
    [InlineData("Variable1,Variable2,Variable3", "Variable2")]
    public async Task EvaluateShouldUseExistingConditionVariablesOnlyAsync(string existingVariables, string conditionVariables)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var ifContent = ValidIfStructure;
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            {
                ConditionalFlowHelper.IfStructureCheckPrompt[..30],
                $"{{\"valid\": true, \"variables\": [\"{string.Join("\",\"", conditionVariables.Split(','))}\"]}}"
            },
            { ConditionalFlowHelper.EvaluateConditionPrompt[..30], "{ \"valid\": true, \"condition\": true }" },
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
        var context = this.CreateSKContext(kernel, contextVariables);
        _ = await target.IfAsync(ifContent, context);

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
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var ifContent = ValidIfStructure;

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
            await target.IfAsync(ifContent, this.CreateSKContext(kernel, contextVariables));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.ContextVariablesNotFound, exception.ErrorCode);
        Assert.Equal($"{nameof(ConditionException.ErrorCodes.ContextVariablesNotFound)}: {string.Join(", ", expectedNotFound)}", exception.Message);
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
