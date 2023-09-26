// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Moq;
using Xunit;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planners.Action.UnitTests;
#pragma warning restore IDE0130 // Namespace does not match folder structure

public sealed class ActionPlannerTests
{
    [Fact]
    public async Task ExtractsAndDeserializesWellFormedJsonFromPlannerResultAsync()
    {
        // Arrange
        var plugins = this.CreateMockFunctionCollection();

        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(ValidPlanString, plugins);

        var planner = new ActionPlanner(kernel.Object);

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

        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(invalidJsonString);

        var planner = new ActionPlanner(kernel.Object);

        // Act & Assert
        await Assert.ThrowsAsync<SKException>(() => planner.CreatePlanAsync("goal"));
    }

    [Fact]
    public void UsesPromptDelegateWhenProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        kernel.Setup(x => x.LoggerFactory).Returns(NullLoggerFactory.Instance);
        var getPromptTemplateMock = new Mock<Func<string>>();
        var config = new ActionPlannerConfig()
        {
            GetPromptTemplate = getPromptTemplateMock.Object
        };

        // Act
        var planner = new ActionPlanner(kernel.Object, config);

        // Assert
        getPromptTemplateMock.Verify(x => x(), Times.Once());
    }

    [Fact]
    public async Task MalformedJsonThrowsAsync()
    {
        // Arrange

        // Extra opening brace before rationale
        string invalidJsonString = @"Here is a possible plan to accomplish the user intent:

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

This plan uses the `GitHubPlugin.PullsList` function to list the open pull requests for the `semantic-kernel` repository owned by `microsoft`. The `state` parameter is set to `""open""` to filter the results to only show open pull requests.
";

        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(invalidJsonString);

        var planner = new ActionPlanner(kernel.Object);

        // Act & Assert
        await Assert.ThrowsAsync<SKException>(async () => await planner.CreatePlanAsync("goal"));
    }

    [Fact]
    public async Task ListOfFunctionsIncludesNativeAndSemanticFunctionsAsync()
    {
        // Arrange
        var plugins = this.CreateMockFunctionCollection();
        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(ValidPlanString, plugins);
        var planner = new ActionPlanner(kernel.Object);
        var context = kernel.Object.CreateNewContext();

        // Act
        var result = await planner.ListOfFunctionsAsync("goal", context);

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}// List pull requests.{Environment.NewLine}GitHubPlugin.PullsList{Environment.NewLine}// List repositories.{Environment.NewLine}GitHubPlugin.RepoList{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    [Fact]
    public async Task ListOfFunctionsExcludesExcludedPluginsAsync()
    {
        // Arrange
        var plugins = this.CreateMockFunctionCollection();
        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(ValidPlanString, plugins);
        var config = new ActionPlannerConfig();
        config.ExcludedPlugins.Add("GitHubPlugin");
        var planner = new ActionPlanner(kernel.Object, config: config);
        var context = kernel.Object.CreateNewContext();

        // Act
        var result = await planner.ListOfFunctionsAsync("goal", context);

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    [Fact]
    public async Task ListOfFunctionsExcludesExcludedFunctionsAsync()
    {
        // Arrange
        var plugins = this.CreateMockFunctionCollection();
        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(ValidPlanString, plugins);
        var config = new ActionPlannerConfig();
        config.ExcludedFunctions.Add("PullsList");
        var planner = new ActionPlanner(kernel.Object, config: config);
        var context = kernel.Object.CreateNewContext();

        // Act
        var result = await planner.ListOfFunctionsAsync("goal", context);

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}// List repositories.{Environment.NewLine}GitHubPlugin.RepoList{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    private Mock<IKernel> CreateMockKernelAndFunctionFlowWithTestString(string testPlanString, Mock<IFunctionCollection>? functions = null)
    {
        var kernel = new Mock<IKernel>();

        if (functions is null)
        {
            functions = new Mock<IFunctionCollection>();
            functions.Setup(x => x.GetFunctionViews()).Returns(new List<FunctionView>());
        }

        var returnContext = new SKContext(kernel.Object,
            new ContextVariables(testPlanString),
            functions.Object
        );

        var context = new SKContext(
            kernel.Object,
            functions: functions.Object
        );

        var mockFunctionFlowFunction = new Mock<ISKFunction>();
        mockFunctionFlowFunction.Setup(x => x.InvokeAsync(
            It.IsAny<SKContext>(),
            null,
            default
        )).Callback<SKContext, object, CancellationToken>(
            (c, s, ct) => c.Variables.Update("Hello world!")
        ).Returns(() => Task.FromResult(new FunctionResult("FunctionName", "PluginName", returnContext, testPlanString)));

        // Mock Functions
        kernel.Setup(x => x.Functions).Returns(functions.Object);
        kernel.Setup(x => x.CreateNewContext()).Returns(context);
        kernel.Setup(x => x.LoggerFactory).Returns(NullLoggerFactory.Instance);

        kernel.Setup(x => x.RegisterSemanticFunction(
            It.IsAny<string>(),
            It.IsAny<string>(),
            It.IsAny<SemanticFunctionConfig>()
        )).Returns(mockFunctionFlowFunction.Object);

        return kernel;
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

    private Mock<IFunctionCollection> CreateMockFunctionCollection()
    {
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("SendEmail", "email", "Send an e-mail", false),
            ("PullsList", "GitHubPlugin", "List pull requests", true),
            ("RepoList", "GitHubPlugin", "List repositories", true),
        };

        var functionsView = new List<FunctionView>();
        var plugins = new Mock<IFunctionCollection>();
        foreach (var (name, pluginName, description, isSemantic) in functions)
        {
            var functionView = new FunctionView(name, pluginName, description);
            var mockFunction = CreateMockFunction(functionView);
            functionsView.Add(functionView);

            mockFunction.Setup(x =>
                    x.InvokeAsync(It.IsAny<SKContext>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()))
                .Returns<SKContext, AIRequestSettings, CancellationToken>((context, settings, CancellationToken) =>
                {
                    context.Variables.Update("MOCK FUNCTION CALLED");
                    return Task.FromResult(new FunctionResult(name, pluginName, context));
                });
            plugins.Setup(x => x.GetFunction(pluginName, name))
                .Returns(mockFunction.Object);
            ISKFunction? outFunc = mockFunction.Object;
            plugins.Setup(x => x.TryGetFunction(pluginName, name, out outFunc)).Returns(true);
        }

        plugins.Setup(x => x.GetFunctionViews()).Returns(functionsView);
        return plugins;
    }

    private const string ValidPlanString = @"Here is a possible plan to accomplish the user intent:
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
