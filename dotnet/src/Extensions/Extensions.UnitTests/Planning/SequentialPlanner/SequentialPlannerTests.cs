// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
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
        kernel.Setup(x => x.RunAsync(It.IsAny<ISKFunction>(), It.IsAny<ContextVariables>(), It.IsAny<CancellationToken>()))
            .Returns<ISKFunction, ContextVariables, CancellationToken>(async (function, vars, cancellationToken) =>
            {
                var functionResult = await function.InvokeAsync(kernel.Object, vars, cancellationToken: cancellationToken);
                return KernelResult.FromFunctionResults(functionResult.GetValue<string>(), new List<FunctionResult> { functionResult });
            });

        var input = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("SendEmail", "email", "Send an e-mail", false),
            ("GetEmailAddress", "email", "Get an e-mail address", false),
            ("Translate", "WriterPlugin", "Translate something", true),
            ("Summarize", "SummarizePlugin", "Summarize something", true)
        };

        var functionsView = new List<FunctionView>();
        var functions = new Mock<IFunctionCollection>();
        foreach (var (name, pluginName, description, isSemantic) in input)
        {
            var functionView = new FunctionView(name, pluginName, description);
            var mockFunction = CreateMockFunction(functionView);
            functionsView.Add(functionView);

            mockFunction.Setup(x =>
                    x.InvokeAsync(It.IsAny<SKContext>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()))
                .Returns<SKContext, object, CancellationToken>((context, settings, cancellationToken) =>
                {
                    context.Variables.Update("MOCK FUNCTION CALLED");
                    return Task.FromResult(new FunctionResult(name, pluginName, context));
                });

            functions.Setup(x => x.GetFunction(It.Is<string>(s => s == pluginName), It.Is<string>(s => s == name)))
                .Returns(mockFunction.Object);
            ISKFunction? outFunc = mockFunction.Object;
            functions.Setup(x => x.TryGetFunction(It.Is<string>(s => s == pluginName), It.Is<string>(s => s == name), out outFunc)).Returns(true);
        }

        functions.Setup(x => x.GetFunctionViews()).Returns(functionsView);

        var expectedFunctions = input.Select(x => x.name).ToList();
        var expectedPlugins = input.Select(x => x.pluginName).ToList();

        var context = new SKContext(
            kernel.Object,
            new ContextVariables(),
            functions.Object
        );

        var returnContext = new SKContext(
            kernel.Object,
            new ContextVariables(),
            functions.Object
        );
        var planString =
            @"
<plan>
    <function.SummarizePlugin.Summarize/>
    <function.WriterPlugin.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function.email.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
    <function.email.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan>";

        returnContext.Variables.Update(planString);

        var mockFunctionFlowFunction = new Mock<ISKFunction>();
        mockFunctionFlowFunction.Setup(x => x.InvokeAsync(
            It.IsAny<SKContext>(),
            null,
            default
        )).Callback<SKContext, object, CancellationToken>(
            (c, s, ct) => c.Variables.Update("Hello world!")
        ).Returns(() => Task.FromResult(new FunctionResult("FunctionName", "PluginName", returnContext, planString)));

        // Mock Plugins
        kernel.Setup(x => x.Functions).Returns(functions.Object);
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
                expectedPlugins.Contains(step.PluginName));

        foreach (var expectedFunction in expectedFunctions)
        {
            Assert.Contains(
                plan.Steps,
                step => step.Name == expectedFunction);
        }

        foreach (var expectedPlugin in expectedPlugins)
        {
            Assert.Contains(
                plan.Steps,
                step => step.PluginName == expectedPlugin);
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
        var functions = new Mock<IFunctionCollection>();

        functions.Setup(x => x.GetFunctionViews()).Returns(new List<FunctionView>());

        var planString = "<plan>notvalid<</plan>";
        var returnContext = new SKContext(
            kernel.Object,
            new ContextVariables(planString),
            functions.Object
        );

        var context = new SKContext(
            kernel.Object,
            new ContextVariables(),
            functions.Object
        );

        var mockFunctionFlowFunction = new Mock<ISKFunction>();
        mockFunctionFlowFunction.Setup(x => x.InvokeAsync(
            It.IsAny<SKContext>(),
            null,
            default
        )).Callback<SKContext, object, CancellationToken>(
            (c, s, ct) => c.Variables.Update("Hello world!")
        ).Returns(() => Task.FromResult(new FunctionResult("FunctionName", "PluginName", returnContext, planString)));

        // Mock Plugins
        kernel.Setup(x => x.Functions).Returns(functions.Object);
        kernel.Setup(x => x.CreateNewContext()).Returns(context);
        kernel.Setup(x => x.RunAsync(It.IsAny<ISKFunction>(), It.IsAny<ContextVariables>(), It.IsAny<CancellationToken>()))
            .Returns<ISKFunction, ContextVariables, CancellationToken>(async (function, vars, cancellationToken) =>
            {
                var functionResult = await function.InvokeAsync(kernel.Object, vars, cancellationToken: cancellationToken);
                return KernelResult.FromFunctionResults(functionResult.GetValue<string>(), new List<FunctionResult> { functionResult });
            });

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
        mockFunction.Setup(x => x.PluginName).Returns(functionView.PluginName);
        return mockFunction;
    }
}
