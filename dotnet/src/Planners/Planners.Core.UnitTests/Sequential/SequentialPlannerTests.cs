// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Reflection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
        var kernel = CreateMockKernel();
        kernel.Setup(x => x.RunAsync(It.IsAny<ContextVariables>(), It.IsAny<CancellationToken>(), It.IsAny<ISKFunction>()))
            .Returns<ContextVariables, CancellationToken, ISKFunction[]>(async (vars, cancellationToken, functions) =>
            {
                var functionResult = await functions[0].InvokeAsync(kernel.Object, vars, cancellationToken: cancellationToken);
                return KernelResult.FromFunctionResults(functionResult.GetValue<string>(), new List<FunctionResult> { functionResult });
            });

        SKPluginCollection plugins = new()
        {
            new SKPlugin("email", new[]
            {
                KernelFunctionFromMethod.Create(() => "MOCK FUNCTION CALLED", "SendEmail", "Send an e-mail"),
                KernelFunctionFromMethod.Create(() => "MOCK FUNCTION CALLED", "GetEmailAddress", "Get an e-mail address")
            }),
            new SKPlugin("WriterPlugin", new[]
            {
                KernelFunctionFromMethod.Create(() => "MOCK FUNCTION CALLED", "Translate", "Translate something")
            }),
            new SKPlugin("SummarizePlugin", new[]
            {
                KernelFunctionFromMethod.Create(() => "MOCK FUNCTION CALLED", "Summarize", "Summarize something")
            })
        };

        var functionRunner = new Mock<IFunctionRunner>();
        var serviceProvider = new Mock<IAIServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        var expectedPlugins = plugins.Select(x => x.Name).ToList();
        var expectedFunctions = plugins.SelectMany(x => x).Select(f => f.Name).ToList();

        var context = new SKContext(
            functionRunner.Object,
            serviceProvider.Object,
            serviceSelector.Object,
            new ContextVariables());

        var returnContext = new SKContext(
            functionRunner.Object,
            serviceProvider.Object,
            serviceSelector.Object,
            new ContextVariables());

        var planString =
            @"
<plan>
    <function.SummarizePlugin.Summarize/>
    <function.WriterPlugin.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function.email.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
    <function.email.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan>";

        returnContext.Variables.Update(planString);

        // Mock Plugins
        kernel.Setup(x => x.Plugins).Returns(plugins);
        kernel.Setup(x => x.CreateNewContext(It.IsAny<ContextVariables>(), It.IsAny<IReadOnlySKPluginCollection>(), It.IsAny<ILoggerFactory>(), It.IsAny<CultureInfo>()))
            .Returns(context);

        var planner = new SequentialPlanner(kernel.Object);
        this.OverwritePlanningFunction(planner, planString);

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
        var kernel = CreateMockKernel();

        var planner = new SequentialPlanner(kernel.Object);

        // Act
        await Assert.ThrowsAsync<SKException>(async () => await planner.CreatePlanAsync(""));
    }

    [Fact]
    public async Task InvalidXMLThrowsAsync()
    {
        // Arrange
        var functionRunner = new Mock<IFunctionRunner>();
        var serviceProvider = new Mock<IAIServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();
        var kernel = new Mock<IKernel>();

        var planString = "<plan>notvalid<</plan>";
        var returnContext = new SKContext(functionRunner.Object, serviceProvider.Object, serviceSelector.Object, new ContextVariables(planString));

        var context = new SKContext(functionRunner.Object, serviceProvider.Object, serviceSelector.Object, new ContextVariables());

        // Mock Plugins
        kernel.Setup(x => x.Plugins).Returns(new SKPluginCollection());
        kernel.Setup(x => x.RunAsync(It.IsAny<ContextVariables>(), It.IsAny<CancellationToken>(), It.IsAny<ISKFunction>()))
            .Returns<ContextVariables, CancellationToken, ISKFunction[]>(async (vars, cancellationToken, functions) =>
            {
                var functionResult = await functions[0].InvokeAsync(kernel.Object, vars, cancellationToken: cancellationToken);
                return KernelResult.FromFunctionResults(functionResult.GetValue<string>(), new List<FunctionResult> { functionResult });
            });

        kernel.Setup(x => x.CreateNewContext(It.IsAny<ContextVariables>(), It.IsAny<IReadOnlySKPluginCollection>(), It.IsAny<ILoggerFactory>(), It.IsAny<CultureInfo>()))
            .Returns(context);

        var planner = new SequentialPlanner(kernel.Object);
        this.OverwritePlanningFunction(planner, planString);

        // Act
        await Assert.ThrowsAsync<SKException>(async () => await planner.CreatePlanAsync("goal"));
    }

    [Fact]
    public void UsesPromptDelegateWhenProvided()
    {
        // Arrange
        var kernel = CreateMockKernel();
        var getPromptTemplateMock = new Mock<Func<string>>();
        var config = new SequentialPlannerConfig()
        {
            GetPromptTemplate = getPromptTemplateMock.Object
        };

        // Act
        var planner = new SequentialPlanner(kernel.Object, config);

        // Assert
        getPromptTemplateMock.Verify(x => x(), Times.Once());
    }

    // Method to create Mock<IKernel> objects
    private static Mock<IKernel> CreateMockKernel()
    {
        var kernel = new Mock<IKernel>();
        kernel.Setup(x => x.LoggerFactory).Returns(NullLoggerFactory.Instance);

        return kernel;
    }

    private void OverwritePlanningFunction(object planner, string planString)
    {
        // This is using private reflection to overwrite the planner's function.
        // If the implementation changes, this will need to be updated as well.
        FieldInfo plannerFunctionField = planner.GetType().GetField("_functionFlowFunction", BindingFlags.Instance | BindingFlags.NonPublic)!;
        Assert.NotNull(plannerFunctionField);
        plannerFunctionField.SetValue(planner, KernelFunctionFromMethod.Create(() => planString, "FunctionName"));
    }
}
