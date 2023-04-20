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
    private const string ValidIfStructure = "<if condition=\"$a equals 0\"><function/></if>";
    private const string ValidWhileStructure = "<while condition=\"$a equals 0\"><function/></while>";

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
    public async Task IfAsyncCanRunIfAsync()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowConstants.EvaluateConditionPrompt[..30], "{\"valid\": true, \"condition\": true}" },
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
    public async Task IfAsyncInvalidConditionJsonPropertyShouldFailAsync(string llmConditionResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowConstants.EvaluateConditionPrompt[..30], llmConditionResult },
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
    public async Task IfAsyncInvalidIfStatementWithoutConditionShouldFailAsync()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");

        // To be able to check the condition need ensure success in the if statement check first
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync("<if condition=\"something\"><function/></if>", this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidCondition, exception.ErrorCode);
    }

    [Theory]
    [InlineData("")]
    [InlineData("Unexpected Result")]
    public async Task IfAsyncInvalidJsonIfStatementCheckResponseShouldFailContextAsync(string llmResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.IfStructureCheckPrompt[..30], llmResult }
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
    public async Task IfAsyncInvalidIfStatementXmlShouldFailAsync(string ifContentInput)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");

        // To be able to check the condition need ensure success in the if statement check first
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
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
    [InlineData("TRUE<while>")]
    [InlineData("<while condition=\"a contains b\">")]
    [InlineData("<whil e condition=\"a contains b\">")]
    [InlineData("<while condition=\"a contains b\"><something></if>")]
    [InlineData("<while condition=\"a contains b\"><something></while>")]
    [InlineData("</while>")]
    public async Task WhileAsyncInvalidStatementXmlShouldFailAsync(string whileContentInput)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");

        var target = new ConditionalFlowHelper(kernel);

        // Act
        var exception = await Assert.ThrowsAsync<XmlException>(async () =>
        {
            await target.WhileAsync(whileContentInput, this.CreateSKContext(kernel));
        });

        // Assert
        Assert.NotNull(exception);
    }

    [Theory]
    [InlineData("<if/>")]
    [InlineData("<if></if>")]
    [InlineData("<if><function/></if>")]
    [InlineData("<if condition=\"\"></if>")]
    [InlineData("<if condition=\"something\"></if>")]
    [InlineData("<if condition=\"something\"><function/></if><else/>")]
    [InlineData("<if condition=\"something\"><function/></if><else></else>")]
    public async Task IfAsyncInvalidIfStatementStructureShouldFailAsync(string ifContentInput)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var target = new ConditionalFlowHelper(kernel);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.IfAsync(ifContentInput, this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidStatementStructure, exception.ErrorCode);
    }

    [Theory]
    [InlineData("<while/>")]
    [InlineData("<while></while>")]
    [InlineData("<while><function/></while>")]
    [InlineData("<while condition=\"\"></while>")]
    [InlineData("<while condition=\"something\"></while>")]
    public async Task WhileAsyncInvalidWhileStatementStructureShouldFailAsync(string whileContentInput)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var target = new ConditionalFlowHelper(kernel);

        // Act
        var exception = await Assert.ThrowsAsync<ConditionException>(async () =>
        {
            await target.WhileAsync(whileContentInput, this.CreateSKContext(kernel));
        });

        // Assert
        Assert.Equal(ConditionException.ErrorCodes.InvalidStatementStructure, exception.ErrorCode);
    }

    [Theory(Skip = "LLM IfStatementCheck is disabled")]
    [InlineData("{\"valid\": false, \"reason\": null}", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("{\"valid\": false, \"reason\": \"\"}", ConditionalFlowHelper.NoReasonMessage)]
    [InlineData("{\"valid\": false, \"reason\": \"Something1 Error\"}", "Something1 Error")]
    [InlineData("{\"valid\": false, \n\"reason\": \"Something2 Error\"}", "Something2 Error")]
    [InlineData("{\"valid\": false, \n\n\"reason\": \"Something3 Error\"}", "Something3 Error")]
    public async Task IfAsyncInvalidIfStatementCheckResponseShouldFailContextWithReasonMessageAsync(string llmResult, string expectedReason)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.IfStructureCheckPrompt[..30], llmResult },
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
    public async Task IfAsyncInvalidEvaluateConditionResponseShouldFailContextWithReasonMessageAsync(string llmResult, string expectedReason)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var ifContent = ValidIfStructure;
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowConstants.EvaluateConditionPrompt[..30], llmResult },
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
    [InlineData("{\"valid\": true, \"condition\": true}", "<if condition=\"$a equals 0\"><functionIf/></if>", "<functionIf />")]
    [InlineData("{\"valid\": true, \"condition\": false}", "<if condition=\"$a equals 0\"><functionIf/></if>", "")]
    [InlineData("{\"valid\": true, \"condition\": true}", "<if condition=\"$a equals 0\"><functionIf/></if><else><functionElse/></else>", "<functionIf />")]
    [InlineData("{\"valid\": true, \"condition\": false}", "<if condition=\"$a equals 0\"><functionIf/></if><else><functionElse/></else>", "<functionElse />")]
    public async Task IfAsyncValidEvaluateConditionResponseShouldReturnAsync(string llmResult, string inputIfStructure, string expectedResult)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.IfStructureCheckPrompt[..30], "{\"valid\": true}" },
            { ConditionalFlowConstants.EvaluateConditionPrompt[..30], llmResult },
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
    [InlineData("Variable1,Variable2", "a")]
    [InlineData("Variable1,Variable2,Variable3", "Variable2")]
    public async Task IfAsyncEvaluateShouldUseExistingConditionVariablesOnlyAsync(string existingVariables, string conditionVariables)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var fakeConditionVariables = string.Join(" AND ", conditionVariables.Split(",").Select(x => $"${x} equals 0"));
        var ifContent = ValidIfStructure.Replace("$a equals 0", fakeConditionVariables, StringComparison.OrdinalIgnoreCase);

        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            {
                ConditionalFlowConstants.IfStructureCheckPrompt[..30],
                $"{{\"valid\": true, \"variables\": [\"{string.Join("\",\"", conditionVariables.Split(','))}\"]}}"
            },
            { ConditionalFlowConstants.EvaluateConditionPrompt[..30], "{ \"valid\": true, \"condition\": true }" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);
        ContextVariables contextVariables = CreateContextVariablesForTest(existingVariables, ifContent);
        IEnumerable<string> notExpectedVariablesInPrompt = GetNotExpectedVariablesInPromptForTest(existingVariables, conditionVariables);

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
                Assert.Contains(variableName, context.Variables["ConditionalVariables"], StringComparison.Ordinal);
            }
        }

        foreach (var variableName in notExpectedVariablesInPrompt)
        {
            Assert.DoesNotContain(variableName, context.Variables["ConditionalVariables"], StringComparison.Ordinal);
        }
    }

    [Theory]
    [InlineData("Variable1,Variable2", "Variable4")]
    [InlineData("Variable1,Variable2,Variable3", "Variable5,Variable2")]
    public async Task IfAsyncEvaluateAsUndefinedWhenConditionVariablesDontExistsAsync(string existingVariables, string conditionVariables)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var fakeConditionVariables = string.Join(" AND ", conditionVariables.Split(",").Select(x => $"${x} equals 0"));
        var ifContent = ValidIfStructure.Replace("$a equals 0", fakeConditionVariables, StringComparison.OrdinalIgnoreCase);

        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            {
                ConditionalFlowConstants.IfStructureCheckPrompt[..30],
                $"{{\"valid\": true, \"variables\": [\"{string.Join("\",\"", conditionVariables.Split(','))}\"]}}"
            },
            { ConditionalFlowConstants.EvaluateConditionPrompt[..30], "{ \"valid\": true, \"condition\": true }" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        ContextVariables contextVariables = CreateContextVariablesForTest(existingVariables, ifContent);
        IEnumerable<string> expectedUndefined = GetExpectedUndefinedForTest(existingVariables, conditionVariables);
        SKContext context = this.CreateSKContext(kernel, contextVariables);

        // Act
        await target.IfAsync(ifContent, context);

        // Assert
        Assert.NotNull(context);
        Assert.True(context.Variables.ContainsKey("ConditionalVariables"));
        foreach (var variableName in expectedUndefined)
        {
            Assert.Contains($"{variableName} = undefined", context.Variables["ConditionalVariables"], StringComparison.Ordinal);
        }
    }

    [Theory]
    [InlineData("Variable1,Variable2", "Variable1")]
    [InlineData("Variable1,Variable2", "a")]
    [InlineData("Variable1,Variable2,Variable3", "Variable2")]
    public async Task WhileAsyncEvaluateShouldUseExistingConditionVariablesOnlyAsync(string existingVariables, string conditionVariables)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var fakeConditionVariables = string.Join(" AND ", conditionVariables.Split(",").Select(x => $"${x} equals 0"));
        var ifContent = ValidWhileStructure.Replace("$a equals 0", fakeConditionVariables, StringComparison.OrdinalIgnoreCase);

        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.EvaluateConditionPrompt[..30], "{ \"valid\": true, \"condition\": true }" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);
        ContextVariables contextVariables = CreateContextVariablesForTest(existingVariables, ifContent);
        IEnumerable<string> notExpectedVariablesInPrompt = GetNotExpectedVariablesInPromptForTest(existingVariables, conditionVariables);

        // Act
        var context = this.CreateSKContext(kernel, contextVariables);
        _ = await target.WhileAsync(ifContent, context);

        // Assert
        Assert.NotNull(context);
        Assert.True(context.Variables.ContainsKey("ConditionalVariables"));
        if (!string.IsNullOrEmpty(conditionVariables))
        {
            foreach (var variableName in conditionVariables.Split(','))
            {
                Assert.Contains(variableName, context.Variables["ConditionalVariables"], StringComparison.Ordinal);
            }
        }

        foreach (var variableName in notExpectedVariablesInPrompt)
        {
            Assert.DoesNotContain(variableName, context.Variables["ConditionalVariables"], StringComparison.Ordinal);
        }
    }

    [Theory]
    [InlineData("Variable1,Variable2", "Variable4")]
    [InlineData("Variable1,Variable2,Variable3", "Variable5,Variable2")]
    public async Task WhileAsyncEvaluateAsUndefinedWhenConditionVariablesDontExistsAsync(string existingVariables, string conditionVariables)
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAITextCompletionService("test", "test", "test");
        var fakeConditionVariables = string.Join(" AND ", conditionVariables.Split(",").Select(x => $"${x} equals 0"));
        var ifContent = ValidWhileStructure.Replace("$a equals 0", fakeConditionVariables, StringComparison.OrdinalIgnoreCase);

        var completionBackendMock = SetupCompletionBackendMock(new Dictionary<string, string>
        {
            { ConditionalFlowConstants.EvaluateConditionPrompt[..30], "{ \"valid\": true, \"condition\": true }" },
        });

        var target = new ConditionalFlowHelper(kernel, completionBackendMock.Object);

        ContextVariables contextVariables = CreateContextVariablesForTest(existingVariables, ifContent);
        IEnumerable<string> expectedUndefined = GetExpectedUndefinedForTest(existingVariables, conditionVariables);
        SKContext context = this.CreateSKContext(kernel, contextVariables);

        // Act
        await target.WhileAsync(ifContent, context);

        // Assert
        Assert.NotNull(context);
        Assert.True(context.Variables.ContainsKey("ConditionalVariables"));
        foreach (var variableName in expectedUndefined)
        {
            Assert.Contains($"{variableName} = undefined", context.Variables["ConditionalVariables"], StringComparison.Ordinal);
        }
    }

    private static IEnumerable<string> GetExpectedUndefinedForTest(string existingVariables, string conditionVariables)
    {
        IEnumerable<string> expectedUndefined = Enumerable.Empty<string>();
        if (!string.IsNullOrEmpty(conditionVariables))
        {
            expectedUndefined = conditionVariables.Split(',').Except(existingVariables?.Split(",") ?? Array.Empty<string>());
        }

        return expectedUndefined;
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

    private static IEnumerable<string> GetNotExpectedVariablesInPromptForTest(string existingVariables, string conditionVariables)
    {
        IEnumerable<string> notExpectedVariablesInPrompt = existingVariables.Split(',');
        if (!string.IsNullOrEmpty(conditionVariables))
        {
            notExpectedVariablesInPrompt = notExpectedVariablesInPrompt.Except(conditionVariables.Split(','));
        }

        return notExpectedVariablesInPrompt;
    }

    private static ContextVariables CreateContextVariablesForTest(string existingVariables, string ifContent)
    {
        var contextVariables = new ContextVariables(ifContent);
        if (!string.IsNullOrEmpty(existingVariables))
        {
            foreach (var variableName in existingVariables.Split(','))
            {
                contextVariables.Set(variableName, "x");
            }
        }

        return contextVariables;
    }
}
