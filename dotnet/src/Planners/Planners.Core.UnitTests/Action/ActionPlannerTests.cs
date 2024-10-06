// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Planning.Action.UnitTests;

public sealed class ActionPlannerTests
{
    [Fact]
    public async Task ExtractsAndDeserializesWellFormedJsonFromPlannerResultAsync()
    {
        // Arrange
        var plugins = this.CreatePluginCollection();

        var kernel = this.CreateKernel(ValidPlanString, plugins);

        var planner = new ActionPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync("goal");

        // Assert
        Assert.Equal("goal", plan.Description);

        Assert.Single(plan.Steps);
        Assert.Equal("GitHubPlugin", plan.Steps[0].PluginName);
        Assert.Equal("PullsList", plan.Steps[0].Name);
    }

    [Fact]
    public async Task InvalidJsonThrowsAsync()
    {
        // Arrange
        string invalidJsonString = "<>";

        var kernel = this.CreateKernel(invalidJsonString);

        var planner = new ActionPlanner(kernel);

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(() => planner.CreatePlanAsync("goal"));
    }

    [Fact]
    public void UsesPromptDelegateWhenProvided()
    {
        // Arrange
        var kernel = this.CreateKernel(string.Empty);

        var getPromptTemplateMock = new Mock<Func<string>>();

        var config = new ActionPlannerConfig()
        {
            GetPromptTemplate = getPromptTemplateMock.Object
        };

        // Act
        var planner = new ActionPlanner(kernel, config);

        // Assert
        getPromptTemplateMock.Verify(x => x(), Times.Once());
    }

    [Fact]
    public async Task MalformedJsonThrowsAsync()
    {
        // Arrange

        // Extra opening brace before rationale
        string invalidJsonString =
            @"Here is a possible plan to accomplish the user intent:
            {
                ""plan"": { {
                    ""rationale"": ""the list contains a function that allows to list pull requests"",
                    ""function"": ""GitHubPlugin.PullsList"",
                    ""parameters"": {
                        ""owner"": ""microsoft"",
                        ""repo"": ""semantic-kernel"",
                        ""state"": ""open""
                    }
                }
            }

            This plan uses the `GitHubPlugin.PullsList` function to list the open pull requests for the `semantic-kernel` repository owned by `microsoft`. The `state` parameter is set to `""open""` to filter the results to only show open pull requests.";

        var kernel = this.CreateKernel(invalidJsonString);

        var planner = new ActionPlanner(kernel);

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(async () => await planner.CreatePlanAsync("goal"));
    }

    [Fact]
    public async Task ListOfFunctionsIncludesNativeAndPromptFunctionsAsync()
    {
        // Arrange
        var plugins = this.CreatePluginCollection();

        var kernel = this.CreateKernel(ValidPlanString, plugins);

        var planner = new ActionPlanner(kernel);

        // Act
        var result = await planner.ListOfFunctionsAsync("goal");

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}// List pull requests.{Environment.NewLine}GitHubPlugin.PullsList{Environment.NewLine}// List repositories.{Environment.NewLine}GitHubPlugin.RepoList{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    [Fact]
    public async Task ListOfFunctionsExcludesExcludedPluginsAsync()
    {
        // Arrange
        var plugins = this.CreatePluginCollection();

        var kernel = this.CreateKernel(ValidPlanString, plugins);

        var config = new ActionPlannerConfig();
        config.ExcludedPlugins.Add("GitHubPlugin");

        var planner = new ActionPlanner(kernel, config: config);

        // Act
        var result = await planner.ListOfFunctionsAsync("goal");

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    [Fact]
    public async Task ListOfFunctionsExcludesExcludedFunctionsAsync()
    {
        // Arrange
        var plugins = this.CreatePluginCollection();

        var kernel = this.CreateKernel(ValidPlanString, plugins);

        var config = new ActionPlannerConfig();
        config.ExcludedFunctions.Add("PullsList");

        var planner = new ActionPlanner(kernel, config: config);

        // Act
        var result = await planner.ListOfFunctionsAsync("goal");

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}// List repositories.{Environment.NewLine}GitHubPlugin.RepoList{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    private Kernel CreateKernel(string testPlanString, KernelPluginCollection? plugins = null)
    {
        plugins ??= new KernelPluginCollection();

        var textResult = new Mock<ITextResult>();
        textResult
            .Setup(tr => tr.GetCompletionAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(testPlanString);

        var textGenerationResult = new List<ITextResult> { textResult.Object };

        var textGeneration = new Mock<ITextGeneration>();
        textGeneration
            .Setup(tc => tc.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(textGenerationResult);

        var serviceSelector = new Mock<IAIServiceSelector>();
        serviceSelector
            .Setup(ss => ss.SelectAIService<ITextGeneration>(It.IsAny<Kernel>(), It.IsAny<ContextVariables>(), It.IsAny<KernelFunction>()))
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
                KernelFunctionFactory.CreateFromMethod(() => "MOCK FUNCTION CALLED", "SendEmail", "Send an e-mail")
            }),
            new KernelPlugin("GitHubPlugin", new[]
            {
                KernelFunctionFactory.CreateFromMethod(() => "MOCK FUNCTION CALLED", "PullsList", "List pull requests"),
                KernelFunctionFactory.CreateFromMethod(() => "MOCK FUNCTION CALLED", "RepoList", "List repositories")
            })
        };
    }

    private const string ValidPlanString =
        @"Here is a possible plan to accomplish the user intent:
        {
            ""plan"":{
                ""rationale"": ""the list contains a function that allows to list pull requests"",
                ""function"": ""GitHubPlugin.PullsList"",
                ""parameters"": {
                    ""owner"": ""microsoft"",
                    ""repo"": ""semantic-kernel"",
                    ""state"": ""open""
                }
            }
        }

        This plan uses the `GitHubPlugin.PullsList` function to list the open pull requests for the `semantic-kernel` repository owned by `microsoft`. The `state` parameter is set to `""open""` to filter the results to only show open pull requests.";
}
