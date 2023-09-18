// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Planning.SequentialPlanner;

public sealed class SequentialPlannerTests
{
    [Theory]
    [InlineData("Write a poem or joke and send it in an e-mail to Kai.")]
    public async Task ItCanCreatePlanAsync(string goal)
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        kernel.Setup(x => x.LoggerFactory).Returns(new Mock<ILoggerFactory>().Object);

        var input = new List<(string name, string skillName, string description, bool isSemantic)>()
        {
            ("SendEmail", "email", "Send an e-mail", false),
            ("GetEmailAddress", "email", "Get an e-mail address", false),
            ("Translate", "WriterSkill", "Translate something", true),
            ("Summarize", "SummarizeSkill", "Summarize something", true)
        };

        var functionsView = new FunctionsView();
        var skills = new Mock<ISkillCollection>();
        foreach (var (name, skillName, description, isSemantic) in input)
        {
            var functionView = new FunctionView(name, skillName, description, new List<ParameterView>(), isSemantic, true);
            var mockFunction = CreateMockFunction(functionView);
            functionsView.AddFunction(functionView);

            mockFunction.Setup(x =>
                    x.InvokeAsync(It.IsAny<SKContext>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
                .Returns<SKContext, CompleteRequestSettings, CancellationToken>((context, settings, cancellationToken) =>
                {
                    context.Variables.Update("MOCK FUNCTION CALLED");
                    return Task.FromResult(context);
                });

            skills.Setup(x => x.GetFunction(It.Is<string>(s => s == skillName), It.Is<string>(s => s == name)))
                .Returns(mockFunction.Object);
            ISKFunction? outFunc = mockFunction.Object;
            skills.Setup(x => x.TryGetFunction(It.Is<string>(s => s == skillName), It.Is<string>(s => s == name), out outFunc)).Returns(true);
        }

        skills.Setup(x => x.GetFunctionsView()).Returns(functionsView);

        var expectedFunctions = input.Select(x => x.name).ToList();
        var expectedSkills = input.Select(x => x.skillName).ToList();

        var context = new SKContext(
            new ContextVariables(),
            skills.Object,
            new Mock<ILoggerFactory>().Object
        );

        var returnContext = new SKContext(
            new ContextVariables(),
            skills.Object,
            new Mock<ILoggerFactory>().Object
        );
        var planString =
            @"
<plan>
    <function.SummarizeSkill.Summarize/>
    <function.WriterSkill.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function.email.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
    <function.email.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan>";

        returnContext.Variables.Update(planString);

        var mockFunctionFlowFunction = new Mock<ISKFunction>();
        mockFunctionFlowFunction.Setup(x => x.InvokeAsync(
            It.IsAny<SKContext>(),
            null,
            default
        )).Callback<SKContext, CompleteRequestSettings, CancellationToken>(
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

        var planner = new Microsoft.SemanticKernel.Planning.SequentialPlanner(kernel.Object);

        // Act
        var plan = await planner.CreatePlanAsync(goal, default);

        // Assert
        Assert.Equal(goal, plan.Description);

        Assert.Contains(
            plan.Steps,
            step =>
                expectedFunctions.Contains(step.Name) &&
                expectedSkills.Contains(step.SkillName));

        foreach (var expectedFunction in expectedFunctions)
        {
            Assert.Contains(
                plan.Steps,
                step => step.Name == expectedFunction);
        }

        foreach (var expectedSkill in expectedSkills)
        {
            Assert.Contains(
                plan.Steps,
                step => step.SkillName == expectedSkill);
        }
    }

    [Fact]
    public async Task EmptyGoalThrowsAsync()
    {
        // Arrange
        var kernel = new Mock<IKernel>();

        var planner = new Microsoft.SemanticKernel.Planning.SequentialPlanner(kernel.Object);

        // Act
        await Assert.ThrowsAsync<SKException>(async () => await planner.CreatePlanAsync(""));
    }

    [Fact]
    public async Task InvalidXMLThrowsAsync()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var skills = new Mock<ISkillCollection>();

        var functionsView = new FunctionsView();
        skills.Setup(x => x.GetFunctionsView()).Returns(functionsView);

        var planString = "<plan>notvalid<</plan>";
        var returnContext = new SKContext(
            new ContextVariables(planString),
            skills.Object,
            new Mock<ILoggerFactory>().Object
        );

        var context = new SKContext(
            new ContextVariables(),
            skills.Object,
            new Mock<ILoggerFactory>().Object
        );

        var mockFunctionFlowFunction = new Mock<ISKFunction>();
        mockFunctionFlowFunction.Setup(x => x.InvokeAsync(
            It.IsAny<SKContext>(),
            null,
            default
        )).Callback<SKContext, CompleteRequestSettings, CancellationToken>(
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

        var planner = new Microsoft.SemanticKernel.Planning.SequentialPlanner(kernel.Object);

        // Act
        await Assert.ThrowsAsync<SKException>(async () => await planner.CreatePlanAsync("goal"));
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
}
