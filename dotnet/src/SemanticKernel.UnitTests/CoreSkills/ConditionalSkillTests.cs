// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests.CoreSkills;

public class ConditionalSkillTests
{
    private readonly ITestOutputHelper _testOutputHelper;

    private const string GoalText = "Solve the equation x^2 = 2.";

    public ConditionalSkillTests(ITestOutputHelper testOutputHelper)
    {
        this._testOutputHelper = testOutputHelper;
        this._testOutputHelper.WriteLine("Tests initialized");
    }

    [Fact]
    public void ItCanBeInstantiated()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");

        // Act - Assert no exception occurs
        _ = new ConditionalSkill(kernel);
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");

        // Act - Assert no exception occurs e.g. due to reflection
        _ = kernel.ImportSkill(new ConditionalSkill(kernel), "condition");
    }

    [Fact]
    public async Task ItCanCreatePlanAsync()
    {
        // Arrange
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var conditionalSkill = new ConditionalSkill(kernel);
        var condition = kernel.ImportSkill(conditionalSkill, "conditional");

        // Act
        var context = await kernel.RunAsync(GoalText, condition["CreatePlan"]);

        // Assert
        var plan = context.Variables.ToPlan();
        Assert.NotNull(plan);
        Assert.NotNull(plan.Id);
        Assert.Equal(GoalText, plan.Goal);
        Assert.StartsWith("<goal>\nSolve the equation x^2 = 2.\n</goal>", plan.PlanString, StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData(
@"<plan>
    <function.MockSkill.Echo input=""Hello World"" />
    <if>
        <dsafd/>
    </if>
</plan>")]
    public async Task InvalidIfResultAsync(string planText)
    {
        // Arrange
        /*var kernelMock = new Mock<IKernel>();
        var memoryMock = new Mock<ISemanticTextMemory>();
        var skillCollectionMock = new Mock<IReadOnlySkillCollection>();
        var loggerMock = new Mock<ILogger>();
        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var target = new ConditionalSkill(kernelMock.Object);
        var functions = kernel.ImportSkill(target);

        var 
        kernelMock.Setup(k => k.RegisterSemanticFunction(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<SemanticFunctionConfig>())).Returns(functions["IfAsync"]);

        //skillCollectionMock.Setup(sc => sc).Returns(skillCollectionMock.Object);
        */
        var aiBackendMock = new Mock<ITextCompletionClient>();

        var kernel = KernelBuilder.Create();
        _ = kernel.Config.AddOpenAICompletionBackend("test", "test", "test");
        var conditionalSkill = new ConditionalSkill(kernel);
        var functions = kernel.ImportSkill(conditionalSkill, "conditional");
        kernel.RegisterSemanticFunction
        aiBackendMock.Setup(a => a.CompleteAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(string.Empty);

        functions["IfAsync"].SetAIBackend(() => aiBackendMock.Object);

        //var context = new SKContext(new ContextVariables(), memoryMock.Object, skillCollectionMock.Object, loggerMock.Object);

        // Act + Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(async () => await kernel.RunAsync(planText, functions["IfAsync"]));
    }

    public class MockSkill
    {
        private readonly ITestOutputHelper _testOutputHelper;

        public MockSkill(ITestOutputHelper testOutputHelper)
        {
            this._testOutputHelper = testOutputHelper;
        }

        [SKFunction("Split the input into two parts")]
        [SKFunctionName("SplitInput")]
        [SKFunctionInput(Description = "The input text to split")]
        public Task<SKContext> SplitInputAsync(string input, SKContext context)
        {
            var parts = input.Split(':');
            context.Variables.Set("First", parts[0]);
            context.Variables.Set("Second", parts[1]);
            return Task.FromResult(context);
        }

        [SKFunction("Echo the input text")]
        [SKFunctionName("Echo")]
        public Task<SKContext> EchoAsync(string text, SKContext context)
        {
            this._testOutputHelper.WriteLine(text);
            _ = context.Variables.Update("Echo Result: " + text);
            return Task.FromResult(context);
        }
    }
}
