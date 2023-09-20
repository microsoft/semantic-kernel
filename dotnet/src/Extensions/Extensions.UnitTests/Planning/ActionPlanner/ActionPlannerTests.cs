// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Action;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Planning.ActionPlanner;

public sealed class ActionPlannerTests
{
    [Fact]
    public async Task ExtractsAndDeserializesWellFormedJsonFromPlannerResultAsync()
    {
        // Arrange
        var skills = this.CreateMockSkillCollection();

        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(ValidPlanString, skills);

        var planner = new Microsoft.SemanticKernel.Planning.ActionPlanner(kernel.Object);

        // Act
        var plan = await planner.CreatePlanAsync("goal");

        // Assert
        Assert.Equal("goal", plan.Description);

        Assert.Single(plan.Steps);
        Assert.Equal("GitHubSkill", plan.Steps[0].SkillName);
        Assert.Equal("PullsList", plan.Steps[0].Name);
    }

    [Fact]
    public async Task InvalidJsonThrowsAsync()
    {
        // Arrange
        string invalidJsonString = "<>";

        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(invalidJsonString);

        var planner = new Microsoft.SemanticKernel.Planning.ActionPlanner(kernel.Object);

        // Act & Assert
        await Assert.ThrowsAsync<SKException>(() => planner.CreatePlanAsync("goal"));
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
        ""function"": ""GitHubSkill.PullsList"",
        ""parameters"": {
            ""owner"": ""microsoft"",
            ""repo"": ""semantic-kernel"",
            ""state"": ""open""
        }
    }
}

This plan uses the `GitHubSkill.PullsList` function to list the open pull requests for the `semantic-kernel` repository owned by `microsoft`. The `state` parameter is set to `""open""` to filter the results to only show open pull requests.
";

        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(invalidJsonString);

        var planner = new Microsoft.SemanticKernel.Planning.ActionPlanner(kernel.Object);

        // Act & Assert
        await Assert.ThrowsAsync<SKException>(async () => await planner.CreatePlanAsync("goal"));
    }

    [Fact]
    public void ListOfFunctionsIncludesNativeAndSemanticFunctions()
    {
        // Arrange
        var skills = this.CreateMockSkillCollection();
        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(ValidPlanString, skills);
        var planner = new Microsoft.SemanticKernel.Planning.ActionPlanner(kernel.Object);
        var context = kernel.Object.CreateNewContext();

        // Act
        var result = planner.ListOfFunctions("goal", context);

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}// List pull requests.{Environment.NewLine}GitHubSkill.PullsList{Environment.NewLine}// List repositories.{Environment.NewLine}GitHubSkill.RepoList{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    [Fact]
    public void ListOfFunctionsExcludesExcludedSkills()
    {
        // Arrange
        var skills = this.CreateMockSkillCollection();
        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(ValidPlanString, skills);
        var config = new ActionPlannerConfig();
        config.ExcludedSkills.Add("GitHubSkill");
        var planner = new Microsoft.SemanticKernel.Planning.ActionPlanner(kernel.Object, config: config);
        var context = kernel.Object.CreateNewContext();

        // Act
        var result = planner.ListOfFunctions("goal", context);

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    [Fact]
    public void ListOfFunctionsExcludesExcludedFunctions()
    {
        // Arrange
        var skills = this.CreateMockSkillCollection();
        var kernel = this.CreateMockKernelAndFunctionFlowWithTestString(ValidPlanString, skills);
        var config = new ActionPlannerConfig();
        config.ExcludedFunctions.Add("PullsList");
        var planner = new Microsoft.SemanticKernel.Planning.ActionPlanner(kernel.Object, config: config);
        var context = kernel.Object.CreateNewContext();

        // Act
        var result = planner.ListOfFunctions("goal", context);

        // Assert
        var expected = $"// Send an e-mail.{Environment.NewLine}email.SendEmail{Environment.NewLine}// List repositories.{Environment.NewLine}GitHubSkill.RepoList{Environment.NewLine}";
        Assert.Equal(expected, result);
    }

    private Mock<IKernel> CreateMockKernelAndFunctionFlowWithTestString(string testPlanString, Mock<ISkillCollection>? skills = null)
    {
        var kernel = new Mock<IKernel>();

        if (skills is null)
        {
            skills = new Mock<ISkillCollection>();

            var functionsView = new FunctionsView();
            skills.Setup(x => x.GetFunctionsView(It.IsAny<bool>(), It.IsAny<bool>())).Returns(functionsView);
        }

        var returnContext = new SKContext(kernel.Object,
            new ContextVariables(testPlanString),
            skills.Object
        );

        var context = new SKContext(
            kernel.Object,
            skills: skills.Object
        );

        var mockFunctionFlowFunction = new Mock<ISKFunction>();
        mockFunctionFlowFunction.Setup(x => x.InvokeAsync(
            It.IsAny<SKContext>(),
            null,
            default
        )).Callback<SKContext, object, CancellationToken>(
            (c, s, ct) => c.Variables.Update("Hello world!")
        ).Returns(() => Task.FromResult(returnContext));

        // Mock Skills
        kernel.Setup(x => x.Skills).Returns(skills.Object);
        kernel.Setup(x => x.CreateNewContext()).Returns(context);

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
        mockFunction.Setup(x => x.SkillName).Returns(functionView.SkillName);
        return mockFunction;
    }

    private Mock<ISkillCollection> CreateMockSkillCollection()
    {
        var functions = new List<(string name, string skillName, string description, bool isSemantic)>()
        {
            ("SendEmail", "email", "Send an e-mail", false),
            ("PullsList", "GitHubSkill", "List pull requests", true),
            ("RepoList", "GitHubSkill", "List repositories", true),
        };

        var functionsView = new FunctionsView();
        var skills = new Mock<ISkillCollection>();
        foreach (var (name, skillName, description, isSemantic) in functions)
        {
            var functionView = new FunctionView(name, skillName, description, new List<ParameterView>(), isSemantic, true);
            var mockFunction = CreateMockFunction(functionView);
            functionsView.AddFunction(functionView);

            mockFunction.Setup(x =>
                    x.InvokeAsync(It.IsAny<SKContext>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()))
                .Returns<SKContext, AIRequestSettings, CancellationToken>((context, settings, CancellationToken) =>
                {
                    context.Variables.Update("MOCK FUNCTION CALLED");
                    return Task.FromResult(context);
                });
            skills.Setup(x => x.GetFunction(skillName, name))
                .Returns(mockFunction.Object);
            ISKFunction? outFunc = mockFunction.Object;
            skills.Setup(x => x.TryGetFunction(skillName, name, out outFunc)).Returns(true);
        }

        skills.Setup(x => x.GetFunctionsView(It.IsAny<bool>(), It.IsAny<bool>())).Returns(functionsView);
        return skills;
    }

    private const string ValidPlanString = @"Here is a possible plan to accomplish the user intent:
{
    ""plan"":{
        ""rationale"": ""the list contains a function that allows to list pull requests"",
        ""function"": ""GitHubSkill.PullsList"",
        ""parameters"": {
            ""owner"": ""microsoft"",
            ""repo"": ""semantic-kernel"",
            ""state"": ""open""
        }
    }
}

This plan uses the `GitHubSkill.PullsList` function to list the open pull requests for the `semantic-kernel` repository owned by `microsoft`. The `state` parameter is set to `""open""` to filter the results to only show open pull requests.";
}
