// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextGeneration;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Planning.Sequential.UnitTests;

public sealed class SequentialPlannerTests
{
    [Theory]
    [InlineData("Write a poem or joke and send it in an e-mail to Kai.")]
    public async Task ItCanCreatePlanAsync(string goal)
    {
        // Arrange
        var plugins = this.CreatePluginCollection();

        var planString =
            @"<plan>
                    <function.SummarizePlugin.Summarize/>
                    <function.WriterPlugin.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
                    <function.email.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
                    <function.email.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
              </plan>";

        var kernel = this.CreateKernel(planString, plugins);

        var planner = new SequentialPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync(goal, default);

        // Assert
        Assert.Equal(goal, plan.Description);

        Assert.Equal(4, plan.Steps.Count);

        Assert.Contains(plan.Steps, step => plugins.TryGetFunction(step.PluginName, step.Name, out var _));
    }

    [Fact]
    public async Task EmptyGoalThrowsAsync()
    {
        // Arrange
        var kernel = this.CreateKernel(string.Empty);

        var planner = new SequentialPlanner(kernel);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => await planner.CreatePlanAsync(""));
    }

    [Fact]
    public async Task InvalidXMLThrowsAsync()
    {
        // Arrange
        var kernel = this.CreateKernel("<plan>notvalid<</plan>");

        var planner = new SequentialPlanner(kernel);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<KernelException>(async () => await planner.CreatePlanAsync("goal"));
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

    private Kernel CreateKernel(string testPlanString, KernelPluginCollection? plugins = null)
    {
        plugins ??= new KernelPluginCollection();

        var textResult = new Mock<ITextResult>();
        textResult
            .Setup(tr => tr.GetCompletionAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(testPlanString);

        var textGenerationResult = new List<ITextResult> { textResult.Object };

        var textGeneration = new Mock<ITextGenerationService>();
        textGeneration
            .Setup(tc => tc.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(textGenerationResult);

        var serviceSelector = new Mock<IAIServiceSelector>();
        serviceSelector
            .Setup(ss => ss.SelectAIService<ITextGenerationService>(It.IsAny<Kernel>(), It.IsAny<ContextVariables>(), It.IsAny<KernelFunction>()))
            .Returns((textGeneration.Object, new PromptExecutionSettings()));

        var serviceCollection = new ServiceCollection();
        serviceCollection.AddSingleton<IAIServiceSelector>(serviceSelector.Object);

        return new Kernel(serviceCollection.BuildServiceProvider(), plugins);
    }

    private KernelPluginCollection CreatePluginCollection()
    {
        return new()
        {
            new KernelPlugin("email", new[]
            {
                KernelFunctionFactory.CreateFromMethod(() => "MOCK FUNCTION CALLED", "SendEmail", "Send an e-mail"),
                KernelFunctionFactory.CreateFromMethod(() => "MOCK FUNCTION CALLED", "GetEmailAddress", "Get an e-mail address")
            }),
            new KernelPlugin("WriterPlugin", new[]
            {
                KernelFunctionFactory.CreateFromMethod(() => "MOCK FUNCTION CALLED", "Translate", "Translate something"),
            }),
            new KernelPlugin("SummarizePlugin", new[]
            {
                KernelFunctionFactory.CreateFromMethod(() => "MOCK FUNCTION CALLED", "Summarize", "Summarize something"),
            })
        };
    }
}
