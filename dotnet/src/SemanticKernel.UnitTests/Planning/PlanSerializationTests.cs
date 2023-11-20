// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Planning;

public sealed class PlanSerializationTests
{
    private readonly Kernel _kernel = new(new Mock<IAIServiceProvider>().Object);
    private readonly Mock<IAIServiceProvider> _serviceProvider = new();
    private readonly Mock<IAIServiceSelector> _serviceSelector = new();

    [Fact]
    public void CanSerializePlan()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var expectedSteps = "\"steps\":[]";
        var plan = new Plan(goal);

        // Act
        var serializedPlan = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan);
        Assert.NotEmpty(serializedPlan);
        Assert.Contains(goal, serializedPlan, StringComparison.OrdinalIgnoreCase);
        Assert.Contains(expectedSteps, serializedPlan, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void CanSerializePlanWithGoalAndSteps()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var expectedSteps = "\"steps\":[{";
        var plan = new Plan(goal, new Mock<ISKFunction>().Object, new Mock<ISKFunction>().Object);

        // Act
        var serializedPlan = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan);
        Assert.NotEmpty(serializedPlan);
        Assert.Contains(goal, serializedPlan, StringComparison.OrdinalIgnoreCase);
        Assert.Contains(expectedSteps, serializedPlan, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void CanSerializePlanWithGoalAndSubPlans()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var expectedSteps = "\"steps\":[{";
        var plan = new Plan(goal, new Plan("Write a poem or joke"), new Plan("Send it in an e-mail to Kai"));

        // Act
        var serializedPlan = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan);
        Assert.NotEmpty(serializedPlan);
        Assert.Contains($"\"description\":\"{goal}\"", serializedPlan, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("\"description\":\"Write a poem or joke\"", serializedPlan, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("\"description\":\"Send it in an e-mail to Kai\"", serializedPlan, StringComparison.OrdinalIgnoreCase);
        Assert.Contains(expectedSteps, serializedPlan, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void CanSerializePlanWithPlanStep()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange Mocks
        var returnContext = new SKContext(this._kernel, this._serviceProvider.Object, this._serviceSelector.Object, new ContextVariables(stepOutput));

        var function = SKFunction.FromMethod(() => { }, "function");

        plan.AddSteps(new Plan(function));

        // Act
        var serializedPlan = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan);
        Assert.NotEmpty(serializedPlan);
        Assert.Contains(goal, serializedPlan, StringComparison.OrdinalIgnoreCase);

        var deserializedPlan = Plan.FromJson(serializedPlan);

        Assert.NotNull(deserializedPlan);
        Assert.Single(deserializedPlan.Steps);
        Assert.Equal("function", deserializedPlan.Steps[0].Name);
    }

    [Fact]
    public void CanSerializePlanWithFunctionStep()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var returnContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables(stepOutput)
        );

        var function = SKFunction.FromMethod(() => { }, "function");

        plan.AddSteps(function);

        // Act
        var serializedPlan = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan);
        Assert.NotEmpty(serializedPlan);
        Assert.Contains(goal, serializedPlan, StringComparison.OrdinalIgnoreCase);

        var deserializedPlan = Plan.FromJson(serializedPlan);

        Assert.NotNull(deserializedPlan);
        Assert.Single(deserializedPlan.Steps);
        Assert.Equal("function", deserializedPlan.Steps[0].Name);
    }

    [Fact]
    public void CanSerializePlanWithFunctionSteps()
    {
        // Arrange// Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var returnContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables(stepOutput)
        );

        var function1 = SKFunction.FromMethod(() => { }, "function1");

        var function2 = SKFunction.FromMethod(() => { }, "function2");

        plan.AddSteps(function1, function2);

        // Act
        var serializedPlan = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan);
        Assert.NotEmpty(serializedPlan);
        Assert.Contains(goal, serializedPlan, StringComparison.OrdinalIgnoreCase);

        var deserializedPlan = Plan.FromJson(serializedPlan);

        Assert.NotNull(deserializedPlan);
        Assert.Equal(2, deserializedPlan.Steps.Count);
        Assert.Equal("function1", deserializedPlan.Steps[0].Name);
        Assert.Equal("function2", deserializedPlan.Steps[1].Name);
    }

    [Fact]
    public void CanSerializePlanWithStepsAndFunction()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var returnContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables(stepOutput)
        );

        var function1 = SKFunction.FromMethod(() => { }, "function1");

        var function2 = SKFunction.FromMethod(() => { }, "function2");

        plan.AddSteps(new Plan(function1), function2);

        // Act
        var serializedPlan = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan);
        Assert.NotEmpty(serializedPlan);
        Assert.Contains(goal, serializedPlan, StringComparison.OrdinalIgnoreCase);

        var deserializedPlan = Plan.FromJson(serializedPlan);

        Assert.NotNull(deserializedPlan);
        Assert.Equal(2, deserializedPlan.Steps.Count);
        Assert.Equal("function1", deserializedPlan.Steps[0].Name);
        Assert.Equal("function2", deserializedPlan.Steps[1].Name);
    }

    [Fact]
    public void CanSerializePlanWithSteps()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var returnContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables(stepOutput)
        );

        var function1 = SKFunction.FromMethod(() => { }, "function1");

        var function2 = SKFunction.FromMethod(() => { }, "function2");

        plan.AddSteps(new Plan(function1), new Plan(function2));

        // Act
        var serializedPlan = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan);
        Assert.NotEmpty(serializedPlan);
    }

    [Fact]
    public async Task CanStepAndSerializePlanWithStepsAsync()
    {
        // Arrange
        var plan = new Plan("Write a poem or joke and send it in an e-mail to Kai.");

        var function = SKFunction.FromMethod(() => { }, "function");

        plan.AddSteps(function, function);

        var serializedPlan1 = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan1);
        Assert.NotEmpty(serializedPlan1);
        Assert.Contains("\"next_step_index\":0", serializedPlan1, StringComparison.OrdinalIgnoreCase);

        var result = await this._kernel.StepAsync("Some input", plan);

        // Act
        var serializedPlan2 = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan2);
        Assert.NotEmpty(serializedPlan2);
        Assert.NotEqual(serializedPlan1, serializedPlan2);
        Assert.Contains("\"next_step_index\":1", serializedPlan2, StringComparison.OrdinalIgnoreCase);

        result = await this._kernel.StepAsync(result);
        var serializedPlan3 = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan3);
        Assert.NotEmpty(serializedPlan3);
        Assert.NotEqual(serializedPlan1, serializedPlan3);
        Assert.NotEqual(serializedPlan2, serializedPlan3);
        Assert.Contains("\"next_step_index\":2", serializedPlan3, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task CanStepAndSerializePlanWithStepsAndContextAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var returnContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables(stepOutput)
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.InvokeAsync(this._kernel, It.IsAny<SKContext>(), null, It.IsAny<CancellationToken>()))
            .Callback<Kernel, SKContext, AIRequestSettings?, CancellationToken>((k, c, s, ct) =>
            {
                c.Variables.TryGetValue("variables", out string? v);
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input + v);
            })
            .Returns(() => Task.FromResult(new FunctionResult("functionName", returnContext)));

        mockFunction.Setup(x => x.Describe()).Returns(new FunctionView("functionName", "pluginName")
        {
            Parameters = new ParameterView[]
            {
                new("variables")
            }
        });

        plan.AddSteps(mockFunction.Object, mockFunction.Object);

        var cv = new ContextVariables(planInput);
        cv.Set("variables", "foo");
        plan = await this._kernel.StepAsync(cv, plan);

        // Act
        var serializedPlan1 = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan1);
        Assert.NotEmpty(serializedPlan1);
        Assert.Contains("\"next_step_index\":1", serializedPlan1, StringComparison.OrdinalIgnoreCase);

        // Act
        cv.Set("variables", "bar");
        cv.Update(string.Empty);
        plan = await this._kernel.StepAsync(cv, plan);

        // Assert
        Assert.NotNull(plan);
        Assert.Equal($"{stepOutput}{planInput}foo{stepOutput}{planInput}foobar", plan.State.ToString());

        // Act
        var serializedPlan2 = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan2);
        Assert.NotEmpty(serializedPlan2);
        Assert.NotEqual(serializedPlan1, serializedPlan2);
        Assert.Contains("\"next_step_index\":2", serializedPlan2, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task CanStepAndSerializeAndDeserializePlanWithStepsAndContextAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var plugins = new SKPluginCollection();

        var returnContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables(stepOutput)
        );

        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.Name).Returns("functionName");
        mockFunction
            .Setup(x => x.InvokeAsync(this._kernel, It.IsAny<SKContext>(), null, It.IsAny<CancellationToken>()))
            .Callback<Kernel, SKContext, AIRequestSettings?, CancellationToken>((k, c, s, ct) =>
            {
                c.Variables.TryGetValue("variables", out string? v);
                returnContext.Variables.Update(returnContext.Variables.Input + c.Variables.Input + v);
            })
            .Returns(() => Task.FromResult(new FunctionResult("functionName", returnContext)));
        mockFunction.Setup(x => x.Describe()).Returns(new FunctionView("functionName", "pluginName"));

        plugins.Add(new SKPlugin("pluginName", new[] { mockFunction.Object }));

        plan.AddSteps(mockFunction.Object, mockFunction.Object);

        var serializedPlan = plan.ToJson();

        var cv = new ContextVariables(planInput);
        cv.Set("variables", "foo");
        plan = await this._kernel.StepAsync(cv, plan);

        // Act
        var serializedPlan1 = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan1);
        Assert.NotEmpty(serializedPlan1);
        Assert.NotEqual(serializedPlan, serializedPlan1);
        Assert.Contains("\"next_step_index\":1", serializedPlan1, StringComparison.OrdinalIgnoreCase);

        // Act
        cv.Set("variables", "bar");
        cv.Update(string.Empty);

        var nextContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables()
        );
        plan = Plan.FromJson(serializedPlan1, plugins);
        plan = await this._kernel.StepAsync(cv, plan);

        // Assert
        Assert.NotNull(plan);
        Assert.Equal($"{stepOutput}{planInput}foo{stepOutput}{planInput}foobar", plan.State.ToString());

        // Act
        var serializedPlan2 = plan.ToJson();

        // Assert
        Assert.NotNull(serializedPlan2);
        Assert.NotEmpty(serializedPlan2);
        Assert.NotEqual(serializedPlan1, serializedPlan2);
        Assert.Contains("\"next_step_index\":2", serializedPlan2, StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void CanDeserializePlan(bool requireFunctions)
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var plugins = new SKPluginCollection();

        var returnContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables(stepOutput)
        );

        var mockFunction = SKFunction.FromMethod((string input) => input + input, "functionName");
        plugins.Add(new SKPlugin("test", new[] { mockFunction }));

        plan.AddSteps(new Plan("Step1", mockFunction), mockFunction);

        // Act
        var serializedPlan = plan.ToJson();
        var deserializedPlan = Plan.FromJson(serializedPlan, plugins, requireFunctions);

        // Assert
        Assert.NotNull(deserializedPlan);
        Assert.Equal(goal, deserializedPlan.Description);

        Assert.Equal(string.Join(",", plan.Outputs),
            string.Join(",", deserializedPlan.Outputs));
        Assert.Equal(string.Join(",", plan.Parameters.Select(kv => $"{kv.Key}:{kv.Value}")),
            string.Join(",", deserializedPlan.Parameters.Select(kv => $"{kv.Key}:{kv.Value}")));
        Assert.Equal(string.Join(",", plan.State.Select(kv => $"{kv.Key}:{kv.Value}")),
            string.Join(",", deserializedPlan.State.Select(kv => $"{kv.Key}:{kv.Value}")));

        Assert.Equal(plan.Steps[0].Name, deserializedPlan.Steps[0].Name);
        Assert.Equal(plan.Steps[1].Name, deserializedPlan.Steps[1].Name);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void DeserializeWithMissingFunctions(bool requireFunctions)
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var stepOutput = "Output: The input was: ";
        var plan = new Plan(goal);

        // Arrange
        var plugins = new SKPluginCollection();

        var returnContext = new SKContext(
            this._kernel, this._serviceProvider.Object, this._serviceSelector.Object,
            new ContextVariables(stepOutput)
        );

        var function = SKFunction.FromMethod((SKContext context) =>
        {
            returnContext.Variables.Update(returnContext.Variables.Input + context.Variables.Input);
        }, "function");

        plan.AddSteps(new Plan("Step1", function), function);

        var serializedPlan = plan.ToJson();

        if (requireFunctions)
        {
            // Act + Assert
            Assert.Throws<SKException>(() => Plan.FromJson(serializedPlan, plugins));
        }
        else
        {
            // Act
            var deserializedPlan = Plan.FromJson(serializedPlan, plugins, requireFunctions);

            // Assert
            Assert.NotNull(deserializedPlan);
            Assert.Equal(goal, deserializedPlan.Description);

            Assert.Equal(string.Join(",", plan.Outputs),
                string.Join(",", deserializedPlan.Outputs));
            Assert.Equal(string.Join(",", plan.Parameters.Select(kv => $"{kv.Key}:{kv.Value}")),
                string.Join(",", deserializedPlan.Parameters.Select(kv => $"{kv.Key}:{kv.Value}")));
            Assert.Equal(string.Join(",", plan.State.Select(kv => $"{kv.Key}:{kv.Value}")),
                string.Join(",", deserializedPlan.State.Select(kv => $"{kv.Key}:{kv.Value}")));

            Assert.Equal(plan.Steps[0].Name, deserializedPlan.Steps[0].Name);
            Assert.Equal(plan.Steps[1].Name, deserializedPlan.Steps[1].Name);
        }
    }
}
