// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Planning.Handlebars;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Planners.UnitTests.Handlebars;

public sealed class HandlebarsPlannerTests
{
    private const string PlanString =
    @"```handlebars
        <plan>
            <function.SummarizePlugin.Summarize/>
            <function.WriterPlugin.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
            <function.email.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
            <function.email.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
        </plan>```";

    [Theory]
    [InlineData("Summarize this text, translate it to French and send it to John Doe.")]
    public async Task ItCanCreatePlanAsync(string goal)
    {
        // Arrange
        var plugins = this.CreatePluginCollection();
        var kernel = this.CreateKernel(PlanString, plugins);
        var planner = new HandlebarsPlanner();

        // Act
        HandlebarsPlan plan = await planner.CreatePlanAsync(kernel, goal);

        // Assert
        Assert.True(!string.IsNullOrEmpty(plan.Prompt));
        Assert.True(!string.IsNullOrEmpty(plan.ToString()));
    }

    [Fact]
    public async Task EmptyGoalThrowsAsync()
    {
        // Arrange
        var kernel = this.CreateKernel(PlanString);

        var planner = new HandlebarsPlanner();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => await planner.CreatePlanAsync(kernel, string.Empty));
    }

    [Fact]
    public async Task InvalidXMLThrowsAsync()
    {
        // Arrange
        var kernel = this.CreateKernel("<plan>notvalid<</plan>");

        var planner = new HandlebarsPlanner();

        // Act & Assert
        var exception = await Assert.ThrowsAsync<KernelException>(async () => await planner.CreatePlanAsync(kernel, "goal"));
        Assert.True(exception?.Message?.Contains("Could not find the plan in the results", StringComparison.InvariantCulture));
    }

    private Kernel CreateKernel(string testPlanString, KernelPluginCollection? plugins = null)
    {
        plugins ??= new KernelPluginCollection();

        var chatMessage = new ChatMessage(AuthorRole.Function, testPlanString);

        var chatResult = new Mock<IChatResult>();
        chatResult
            .Setup(cr => cr.GetChatMessageAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(chatMessage);

        var chatCompletionResult = new List<IChatResult> { chatResult.Object };

        var chatCompletion = new Mock<IChatCompletion>();
        chatCompletion
            .Setup(cc => cc.GetChatCompletionsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(chatCompletionResult);
        chatCompletion
            .Setup(cc => cc.CreateNewChat(It.IsAny<string>()))
            .Returns(new ChatHistory());

        var serviceSelector = new Mock<IAIServiceSelector>();
        serviceSelector
            .Setup(ss => ss.SelectAIService<IChatCompletion>(It.IsAny<Kernel>(), It.IsAny<KernelFunction>(), It.IsAny<KernelFunctionArguments>()))
            .Returns((chatCompletion.Object, new PromptExecutionSettings()));

        var serviceCollection = new ServiceCollection();
        serviceCollection.AddSingleton<IAIServiceSelector>(serviceSelector.Object);
        serviceCollection.AddSingleton<IChatCompletion>(chatCompletion.Object);

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
