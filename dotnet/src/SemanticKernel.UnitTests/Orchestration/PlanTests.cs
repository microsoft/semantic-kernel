// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Orchestration;

public sealed class PlanTests
{
    [Fact]
    public Task CanCreatePlanAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        // Act
        var plan = new Plan(goal);

        // Assert
        Assert.Equal(goal, plan.Description);
        Assert.Empty(plan.Steps);
        return Task.CompletedTask;
    }

    [Fact]
    public async Task CanExecutePlanAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal);

        // Act
        var result = await plan.InvokeAsync("Some input");

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Some input", result.Result);
    }

    [Fact]
    public async Task CanExecutePlanWithPlanStepAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));

        plan.AddSteps(new Plan(mockFunction.Object));

        // Act
        var result = await plan.InvokeAsync(planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"{stepOutput}{planInput}", result.Result);
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Once);
    }

    [Fact]
    public async Task CanExecutePlanWithFunctionStepAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));

        plan.AddSteps(mockFunction.Object);

        // Act
        var result = await plan.InvokeAsync(planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"{stepOutput}{planInput}", result.Result);
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Once);
    }

    [Fact]
    public async Task CanExecutePlanWithFunctionStepsAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));

        plan.AddSteps(mockFunction.Object, mockFunction.Object);

        // Act
        var result = await plan.InvokeAsync(planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"{stepOutput}{planInput}{stepOutput}{planInput}", result.Result);
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Exactly(2));
    }

    [Fact]
    public async Task CanExecutePlanWithStepsAndFunctionAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));

        plan.AddSteps(new Plan(mockFunction.Object), mockFunction.Object);

        // Act
        var result = await plan.InvokeAsync(planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"{stepOutput}{planInput}{stepOutput}{planInput}", result.Result);
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Exactly(2));
    }

    [Fact]
    public async Task CanExecutePlanWithStepsAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));

        plan.AddSteps(new Plan(mockFunction.Object), new Plan(mockFunction.Object));

        // Act
        var result = await plan.InvokeAsync(planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"{stepOutput}{planInput}{stepOutput}{planInput}", result.Result);
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Exactly(2));
    }

    [Fact]
    public async Task CanStepPlanWithStepsAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));

        plan.AddSteps(mockFunction.Object, mockFunction.Object);

        // Act
        var result = await kernel.Object.StepAsync(planInput, plan);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"{stepOutput}{planInput}", result.State.ToString());

        // Act
        result = await kernel.Object.StepAsync(result);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"{stepOutput}{planInput}{stepOutput}{planInput}", result.State.ToString());
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Exactly(2));
    }

    [Fact]
    public async Task CanStepPlanWithStepsAndContextAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
            {
                c.Variables.Get("variables", out var v);
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input + v);
            })
            .Returns(() => Task.FromResult(returnContext));
        mockFunction.Setup(x => x.Describe()).Returns(new FunctionView()
        { Parameters = new List<ParameterView>() { new ParameterView() { Name = "variables" } } });

        plan.AddSteps(mockFunction.Object, mockFunction.Object);

        // Act
        var cv = new ContextVariables(planInput);
        cv.Set("variables", "foo");
        plan = await kernel.Object.StepAsync(cv, plan);

        // Assert
        Assert.NotNull(plan);
        Assert.Equal($"{stepOutput}{planInput}foo", plan.State.ToString());

        // Act
        cv.Set("variables", "bar");
        cv.Update(string.Empty);
        plan = await kernel.Object.StepAsync(cv, plan);

        // Assert
        Assert.NotNull(plan);
        Assert.Equal($"{stepOutput}{planInput}foo{stepOutput}{planInput}foobar", plan.State.ToString());
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Exactly(2));
    }

    [Fact]
    public async Task StepExceptionIsThrownAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        returnContext.Fail("Error description", new ArgumentException("Error message"));

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Returns(() => Task.FromResult(returnContext));

        plan.AddSteps(mockFunction.Object, mockFunction.Object);

        // Act
        var cv = new ContextVariables(planInput);
        await Assert.ThrowsAsync<KernelException>(async () => await kernel.Object.StepAsync(cv, plan));
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Once);
    }

    [Fact]
    public async Task PlanStepExceptionIsThrownAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(stepOutput),
            memory.Object,
            skills.Object,
            log.Object
        );

        returnContext.Fail("Error description", new ArgumentException("Error message"));

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Returns(() => Task.FromResult(returnContext));

        plan.AddSteps(new Plan(mockFunction.Object), new Plan(mockFunction.Object));

        // Act
        var cv = new ContextVariables(planInput);
        await Assert.ThrowsAsync<KernelException>(async () => await kernel.Object.StepAsync(cv, plan));
        mockFunction.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Once);
    }

    [Fact]
    public async Task CanExecutePanWithTreeStepsAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal);
        var subPlan = new Plan("Write a poem or joke");

        // Arrange
        var kernel = new Mock<IKernel>();
        var log = new Mock<ILogger>();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();

        var returnContext = new SKContext(
            new ContextVariables(),
            memory.Object,
            skills.Object,
            log.Object
        );

        var childFunction1 = new Mock<ISKFunction>();
        childFunction1.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update("Child 1 output!" + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));
        var childFunction2 = new Mock<ISKFunction>();
        childFunction2.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update("Child 2 is happy about " + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));
        var childFunction3 = new Mock<ISKFunction>();
        childFunction3.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update("Child 3 heard " + c.Variables.Input))
            .Returns(() => Task.FromResult(returnContext));

        var nodeFunction1 = new Mock<ISKFunction>();
        nodeFunction1.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null))
            .Callback<SKContext, CompleteRequestSettings, ILogger, CancellationToken?>((c, s, l, ct) =>
                returnContext.Variables.Update(c.Variables.Input + " - this just happened."))
            .Returns(() => Task.FromResult(returnContext));

        subPlan.AddSteps(childFunction1.Object, childFunction2.Object, childFunction3.Object);
        plan.AddSteps(subPlan);
        plan.AddSteps(nodeFunction1.Object);

        // Act
        while (plan.HasNextStep)
        {
            plan = await kernel.Object.StepAsync(plan);
        }

        // Assert
        Assert.NotNull(plan);
        Assert.Equal($"Child 3 heard Child 2 is happy about Child 1 output!Write a poem or joke - this just happened.", plan.State.ToString());
        nodeFunction1.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Once);
        childFunction1.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Once);
        childFunction2.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Once);
        childFunction3.Verify(x => x.InvokeAsync(It.IsAny<SKContext>(), null, null, null), Times.Once);
    }

    [Fact]
    public void CanCreatePlanWithGoalAndSteps()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal, new Mock<ISKFunction>().Object, new Mock<ISKFunction>().Object);

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goal, plan.Description);
        Assert.Equal(2, plan.Steps.Count);
    }

    [Fact]
    public void CanCreatePlanWithGoalAndSubPlans()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal, new Plan("Write a poem or joke"), new Plan("Send it in an e-mail to Kai"));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goal, plan.Description);
        Assert.Equal(2, plan.Steps.Count);
    }
}
