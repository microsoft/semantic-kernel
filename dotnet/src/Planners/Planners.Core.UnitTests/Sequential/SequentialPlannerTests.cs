// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planners.Sequential.UnitTests;
#pragma warning restore IDE0130 // Namespace does not match folder structure

public sealed class SequentialPlannerTests
{
    [Theory]
    [InlineData("Write a poem or joke and send it in an e-mail to Kai.")]
    public async Task ItCanCreatePlanAsync(string goal)
    {
        // Arrange
        var functionCollection = this.CreateFunctionCollection();

        var planString =
            @"<plan>
                    <function.SummarizePlugin.Summarize/>
                    <function.WriterPlugin.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
                    <function.email.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
                    <function.email.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
              </plan>";

        var kernel = this.CreateKernel(planString, functionCollection);

        var planner = new SequentialPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync(goal, default);

        // Assert
        Assert.Equal(goal, plan.Description);

        Assert.Equal(4, plan.Steps.Count);

        Assert.Contains(plan.Steps, step => functionCollection.TryGetFunction(step.PluginName, step.Name, out var _));
    }

    [Fact]
    public async Task EmptyGoalThrowsAsync()
    {
        // Arrange
        var kernel = this.CreateKernel(string.Empty);

        var planner = new SequentialPlanner(kernel);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<SKException>(async () => await planner.CreatePlanAsync(""));
        Assert.Equal("The goal specified is empty", exception.Message);
    }

    [Fact]
    public async Task InvalidXMLThrowsAsync()
    {
        // Arrange
        var kernel = this.CreateKernel("<plan>notvalid<</plan>");

        var planner = new SequentialPlanner(kernel);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<SKException>(async () => await planner.CreatePlanAsync("goal"));
        Assert.True(exception?.InnerException?.Message?.Contains("Failed to parse plan xml strings", StringComparison.InvariantCulture));
    }

    [Fact]
    public void UsesPromptDelegateWhenProvided()
    {
        // Arrange
        var kernel = this.CreateKernel(string.Empty);
        var getPromptTemplateMock = new Mock<Func<string>>();
        var config = new SequentialPlannerConfig()
        {
            GetPromptTemplate = getPromptTemplateMock.Object
        };

        // Act
        var planner = new SequentialPlanner(kernel, config);

        // Assert
        getPromptTemplateMock.Verify(x => x(), Times.Once());
    }

    private Kernel CreateKernel(string testPlanString, FunctionCollection? functions = null)
    {
        if (functions is null)
        {
            functions = new FunctionCollection();
        }

        var textResult = new Mock<ITextResult>();
        textResult
            .Setup(tr => tr.GetCompletionAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(testPlanString);

        var textCompletionResult = new List<ITextResult> { textResult.Object };

        var textCompletion = new Mock<ITextCompletion>();
        textCompletion
            .Setup(tc => tc.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(textCompletionResult);

        var serviceSelector = new Mock<IAIServiceSelector>();
        serviceSelector
            .Setup(ss => ss.SelectAIService<ITextCompletion>(It.IsAny<SKContext>(), It.IsAny<ISKFunction>()))
            .Returns((textCompletion.Object, new AIRequestSettings()));

        var functionRunner = new Mock<IFunctionRunner>();
        var serviceProvider = new Mock<IAIServiceProvider>();

        return new Kernel(serviceProvider.Object, functions, serviceSelector.Object);
    }

    private FunctionCollection CreateFunctionCollection()
    {
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("SendEmail", "email", "Send an e-mail", false),
            ("GetEmailAddress", "email", "Get an e-mail address", false),
            ("Translate", "WriterPlugin", "Translate something", true),
            ("Summarize", "SummarizePlugin", "Summarize something", true)
        };

        var collection = new FunctionCollection();

        foreach (var (name, pluginName, description, isSemantic) in functions)
        {
            var functionView = new FunctionView(name, pluginName, description);
            var mockFunction = CreateMockFunction(functionView);

            mockFunction.Setup(x => x.InvokeAsync(
                It.IsAny<SKContext>(),
                It.IsAny<AIRequestSettings?>(),
                It.IsAny<CancellationToken>()))
                .Returns<
                    SKContext,
                    AIRequestSettings,
                    CancellationToken>((context, settings, CancellationToken) =>
                    {
                        return Task.FromResult(new FunctionResult(name, pluginName, context));
                    });

            collection.AddFunction(mockFunction.Object);
        }

        return collection;
    }

    // Method to create Mock<ISKFunction> objects
    private static Mock<ISKFunction> CreateMockFunction(FunctionView functionView)
    {
        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.Describe()).Returns(functionView);
        mockFunction.Setup(x => x.Name).Returns(functionView.Name);
        mockFunction.Setup(x => x.PluginName).Returns(functionView.PluginName);
        return mockFunction;
    }
}
