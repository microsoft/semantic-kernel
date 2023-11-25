// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Planners.UnitTests.Planning;

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
    public async Task CanExecutePlanWithContextAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal);

        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var variables = new ContextVariables("Some input");

        // Act
        var result = await plan.InvokeAsync(kernel, variables);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Some input", variables.Input);
        Assert.Null(result.GetValue<string>());

        plan = new Plan(goal);
        // Act
        variables.Update("other input");
        result = await plan.InvokeAsync(kernel, variables);
        // Assert
        Assert.NotNull(result);
        Assert.Equal("other input", variables.Input);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task CanExecutePlanWithPlanStepAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var actualInput = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            actualInput = variables.Input;
            return "fake result";
        }, "function");

        plan.AddSteps(new Plan(function));

        // Act
        var result = await plan.InvokeAsync(kernel, planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake result", result.GetValue<string>());
        Assert.Equal(planInput, actualInput);
    }

    [Fact]
    public async Task CanExecutePlanWithFunctionStepAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal(planInput, variables.Input);
            return "fake result";
        }, "function");

        plan.AddSteps(function);

        // Act
        var result = await plan.InvokeAsync(kernel, planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake result", result.GetValue<string>());
    }

    [Fact]
    public async Task CanExecutePlanWithFunctionStepsAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function1 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal(planInput, variables.Input);
            return "fake result of function 1";
        }, "function1");

        var function2 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal("fake result of function 1", variables.Input);
            return "fake result of function2";
        }, "function2");

        plan.AddSteps(function1, function2);

        // Act
        var result = await plan.InvokeAsync(kernel, planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake result of function2", result.GetValue<string>());
    }

    [Fact]
    public async Task CanExecutePlanWithStepsAndFunctionAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function1 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal(planInput, variables.Input);
            return "fake result of function 1";
        }, "function1");

        var function2 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal("fake result of function 1", variables.Input);
            return "fake result of function2";
        }, "function2");

        plan.AddSteps(new Plan(function1), new Plan(function2));

        // Act
        var result = await plan.InvokeAsync(kernel, planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake result of function2", result.GetValue<string>());
    }

    [Fact]
    public async Task CanExecutePlanWithStepsAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function1 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal(planInput, variables.Input);
            return "fake result of function 1";
        }, "function1");

        var function2 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal("fake result of function 1", variables.Input);
            return "fake result of function2";
        }, "function2");

        plan.AddSteps(new Plan(function1), new Plan(function2));

        // Act
        var result = await plan.InvokeAsync(kernel, planInput);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake result of function2", result.GetValue<string>());
    }

    [Fact]
    public async Task CanStepPlanWithStepsAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function1 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal(planInput, variables.Input);
            return "fake result of function 1";
        }, "function1");

        var function2 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal("fake result of function 1", variables.Input);
            return "fake result of function2";
        }, "function2");

        plan.AddSteps(function1, function2);

        // Act
        var result = await kernel.StepAsync(planInput, plan);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake result of function 1", result.State.ToString());

        // Act
        result = await kernel.StepAsync(result);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake result of function2", result.State.ToString());
    }

    [Fact]
    public async Task CanStepPlanWithStepsAndContextAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function1 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal(planInput, variables.Input);
            Assert.Equal("foo", variables["variables"]);

            return "fake result of function 1";
        }, "function1");

        var function2 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            Assert.Equal("fake result of function 1", variables.Input);
            Assert.Equal("bar", variables["variables"]);

            return "fake result of function2";
        }, "function2");

        plan.AddSteps(function1, function2);

        // Act
        var cv = new ContextVariables(planInput);
        cv.Set("variables", "foo");
        plan = await kernel.StepAsync(cv, plan);

        // Assert
        Assert.NotNull(plan);
        Assert.Equal("fake result of function 1", plan.State.ToString());

        // Act
        cv.Set("variables", "bar");
        cv.Update(string.Empty);
        plan = await kernel.StepAsync(cv, plan);

        // Assert
        Assert.NotNull(plan);
        Assert.Equal("fake result of function2", plan.State.ToString());
    }

    [Fact]
    public async Task StepExceptionIsThrownAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        static void method() => throw new ArgumentException("Error message");
        var function = KernelFunctionFactory.CreateFromMethod(method, "function", "description");

        plan.AddSteps(function, function);

        // Act
        var cv = new ContextVariables(planInput);
        await Assert.ThrowsAsync<ArgumentException>(async () => await kernel.StepAsync(cv, plan));
    }

    [Fact]
    public async Task PlanStepExceptionIsThrownAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var planInput = "Some input";
        var plan = new Plan(goal);

        // Arrange
        var logger = new Mock<ILogger>();
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        static void method() => throw new ArgumentException("Error message");
        var function = KernelFunctionFactory.CreateFromMethod(method, "function", "description");

        plan.AddSteps(new Plan(function), new Plan(function));

        // Act
        var cv = new ContextVariables(planInput);
        await Assert.ThrowsAsync<ArgumentException>(async () => await kernel.StepAsync(cv, plan));
    }

    [Fact]
    public async Task CanExecutePlanWithTreeStepsAsync()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal);
        var subPlan = new Plan("Write a poem or joke");

        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var childFunction1 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return "Child 1 output!" + variables.Input;
        },
        "childFunction1");

        var childFunction2 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return "Child 2 is happy about " + variables.Input;
        },
        "childFunction2");

        var childFunction3 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return "Child 3 heard " + variables.Input;
        },
        "childFunction3");

        var nodeFunction1 = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return variables.Input + " - this just happened.";
        },
        "nodeFunction1");

        subPlan.AddSteps(childFunction1, childFunction2, childFunction3);
        plan.AddSteps(subPlan);
        plan.AddSteps(nodeFunction1);

        // Act
        while (plan.HasNextStep)
        {
            plan = await kernel.StepAsync(plan);
        }

        // Assert
        Assert.NotNull(plan);
        Assert.Equal("Child 3 heard Child 2 is happy about Child 1 output!Write a poem or joke - this just happened.", plan.State.ToString());
    }

    [Fact]
    public void CanCreatePlanWithGoalAndSteps()
    {
        // Arrange
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var function1 = KernelFunctionFactory.CreateFromMethod(() => true);
        var function2 = KernelFunctionFactory.CreateFromMethod(() => true);
        var plan = new Plan(goal, function1, function2);

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

    [Fact]
    public async Task CanExecutePlanWithOneStepAndStateAsync()
    {
        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return "Here is a poem about " + variables.Input;
        },
        "function");

        var plan = new Plan(function);
        plan.State.Set("input", "Cleopatra");

        // Act
        var result = await plan.InvokeAsync(kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Here is a poem about Cleopatra", result.GetValue<string>());
    }

    [Fact]
    public async Task CanExecutePlanWithStateAsync()
    {
        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            variables.TryGetValue("type", out string? t);
            return $"Here is a {t} about " + variables.Input;
        },
        "function");

        var planStep = new Plan(function);
        planStep.Parameters.Set("type", string.Empty);

        var plan = new Plan(string.Empty);
        plan.AddSteps(planStep);
        plan.State.Set("input", "Cleopatra");
        plan.State.Set("type", "poem");

        // Act
        var result = await plan.InvokeAsync(kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Here is a poem about Cleopatra", result.GetValue<string>());
    }

    [Fact]
    public async Task CanExecutePlanWithCustomContextAsync()
    {
        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            variables.TryGetValue("type", out string? t);
            return $"Here is a {t} about " + variables.Input;
        },
        "function");

        var plan = new Plan(function);
        plan.State.Set("input", "Cleopatra");
        plan.State.Set("type", "poem");

        // Act
        var result = await plan.InvokeAsync(kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Here is a poem about Cleopatra", result.GetValue<string>());

        plan = new Plan(function);
        plan.State.Set("input", "Cleopatra");
        plan.State.Set("type", "poem");

        var variablesOverride = new ContextVariables();
        variablesOverride.Set("type", "joke");
        variablesOverride.Update("Medusa");

        // Act
        result = await plan.InvokeAsync(kernel, variablesOverride);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Here is a joke about Medusa", result.GetValue<string>());
    }

    [Fact]
    public async Task CanExecutePlanWithCustomStateAsync()
    {
        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            variables.TryGetValue("type", out string? t);
            return $"Here is a {t} about " + variables.Input;
        },
        "function");

        var planStep = new Plan(function);
        planStep.Parameters.Set("type", string.Empty);
        var plan = new Plan("A plan");
        plan.State.Set("input", "Medusa");
        plan.State.Set("type", "joke");
        plan.AddSteps(planStep);

        // Act
        var result = await plan.InvokeAsync(kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Here is a joke about Medusa", result.GetValue<string>());

        planStep = new Plan(function);
        plan = new Plan("A plan");
        planStep.Parameters.Set("input", "Medusa");
        planStep.Parameters.Set("type", "joke");
        plan.State.Set("input", "Cleopatra"); // state input will not override parameter
        plan.State.Set("type", "poem");
        plan.AddSteps(planStep);

        // Act
        result = await plan.InvokeAsync(kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Here is a poem about Medusa", result.GetValue<string>());

        planStep = new Plan(function);
        plan = new Plan("A plan");
        planStep.Parameters.Set("input", "Cleopatra");
        planStep.Parameters.Set("type", "poem");
        plan.AddSteps(planStep);

        var variablesOverride = new ContextVariables();
        variablesOverride.Set("type", "joke");
        variablesOverride.Update("Medusa"); // context input will not override parameters

        // Act
        result = await plan.InvokeAsync(kernel, variablesOverride);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Here is a joke about Cleopatra", result.GetValue<string>());
    }

    [Fact]
    public async Task CanExecutePlanWithJoinedResultAsync()
    {
        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var outlineFunction = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return $"Here is a {variables["chapterCount"]} chapter outline about " + variables.Input;
        },
        "outlineFunction");

        var elementAtIndexFunction = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return $"Outline section #{variables["index"]} of {variables["count"]}: " + variables.Input;
        },
        "elementAtIndexFunction");

        var novelChapterFunction = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return $"Chapter #{variables["chapterIndex"]}: {variables.Input}\nTheme:{variables["theme"]}\nPreviously:{variables["previousChapter"]}";
        },
        "novelChapterFunction");

        var plan = new Plan("A plan with steps that alternate appending to the plan result.");

        // Steps:
        // - WriterPlugin.NovelOutline chapterCount='3' INPUT='A group of kids in a club called 'The Thinking Caps' that solve mysteries and puzzles using their creativity and logic.' endMarker='<!--===ENDPART===-->' => OUTLINE
        // - MiscPlugin.ElementAtIndex count='3' INPUT='$OUTLINE' index='0' => CHAPTER_1_SYNOPSIS
        // - WriterPlugin.NovelChapter chapterIndex='1' previousChapter='' INPUT='$CHAPTER_1_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_1
        // - MiscPlugin.ElementAtIndex count='3' INPUT='$OUTLINE' index='1' => CHAPTER_2_SYNOPSIS
        // - WriterPlugin.NovelChapter chapterIndex='2' previousChapter='$CHAPTER_1_SYNOPSIS' INPUT='$CHAPTER_2_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_2
        // - MiscPlugin.ElementAtIndex count='3' INPUT='$OUTLINE' index='2' => CHAPTER_3_SYNOPSIS
        // - WriterPlugin.NovelChapter chapterIndex='3' previousChapter='$CHAPTER_2_SYNOPSIS' INPUT='$CHAPTER_3_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_3
        var planStep = new Plan(outlineFunction);
        planStep.Parameters.Set("input",
            "NovelOutline function input.");
        planStep.Parameters.Set("chapterCount", "3");
        planStep.Outputs.Add("OUTLINE");
        plan.AddSteps(planStep);

        planStep = new Plan(elementAtIndexFunction);
        planStep.Parameters.Set("count", "3");
        planStep.Parameters.Set("INPUT", "$OUTLINE");
        planStep.Parameters.Set("index", "0");
        planStep.Outputs.Add("CHAPTER_1_SYNOPSIS");
        plan.AddSteps(planStep);

        planStep = new Plan(novelChapterFunction);
        planStep.Parameters.Set("chapterIndex", "1");
        planStep.Parameters.Set("previousChapter", " ");
        planStep.Parameters.Set("INPUT", "$CHAPTER_1_SYNOPSIS");
        planStep.Parameters.Set("theme", "Children's mystery");
        planStep.Outputs.Add("RESULT__CHAPTER_1");
        plan.Outputs.Add("RESULT__CHAPTER_1");
        plan.AddSteps(planStep);

        planStep = new Plan(elementAtIndexFunction);
        planStep.Parameters.Set("count", "3");
        planStep.Parameters.Set("INPUT", "$OUTLINE");
        planStep.Parameters.Set("index", "1");
        planStep.Outputs.Add("CHAPTER_2_SYNOPSIS");
        plan.AddSteps(planStep);

        planStep = new Plan(novelChapterFunction);
        planStep.Parameters.Set("chapterIndex", "2");
        planStep.Parameters.Set("previousChapter", "$CHAPTER_1_SYNOPSIS");
        planStep.Parameters.Set("INPUT", "$CHAPTER_2_SYNOPSIS");
        planStep.Parameters.Set("theme", "Children's mystery");
        planStep.Outputs.Add("RESULT__CHAPTER_2");
        plan.Outputs.Add("RESULT__CHAPTER_2");
        plan.AddSteps(planStep);

        planStep = new Plan(elementAtIndexFunction);
        planStep.Parameters.Set("count", "3");
        planStep.Parameters.Set("INPUT", "$OUTLINE");
        planStep.Parameters.Set("index", "2");
        planStep.Outputs.Add("CHAPTER_3_SYNOPSIS");
        plan.AddSteps(planStep);

        planStep = new Plan(novelChapterFunction);
        planStep.Parameters.Set("chapterIndex", "3");
        planStep.Parameters.Set("previousChapter", "$CHAPTER_2_SYNOPSIS");
        planStep.Parameters.Set("INPUT", "$CHAPTER_3_SYNOPSIS");
        planStep.Parameters.Set("theme", "Children's mystery");
        planStep.Outputs.Add("CHAPTER_3");
        plan.Outputs.Add("CHAPTER_3");
        plan.AddSteps(planStep);

        // Act
        var result = await plan.InvokeAsync(kernel);

        var expected =
            @"Chapter #1: Outline section #0 of 3: Here is a 3 chapter outline about NovelOutline function input.
Theme:Children's mystery
Previously:
Chapter #2: Outline section #1 of 3: Here is a 3 chapter outline about NovelOutline function input.
Theme:Children's mystery
Previously:Outline section #0 of 3: Here is a 3 chapter outline about NovelOutline function input.
Chapter #3: Outline section #2 of 3: Here is a 3 chapter outline about NovelOutline function input.
Theme:Children's mystery
Previously:Outline section #1 of 3: Here is a 3 chapter outline about NovelOutline function input.";

        // Assert
        var res = result.GetValue<string>();
        Assert.Equal(expected, result.GetValue<string>());
        Assert.True(result.TryGetMetadataValue<string>("RESULT__CHAPTER_1", out var chapter1));
        Assert.True(result.TryGetMetadataValue<string>("RESULT__CHAPTER_2", out var chapter2));
        Assert.True(result.TryGetMetadataValue<string>("CHAPTER_3", out var chapter3));
        Assert.False(result.TryGetMetadataValue<string>("CHAPTER_3_SYNOPSIS", out var chapter3Synopsis));
    }

    [Fact]
    public async Task CanExecutePlanWithExpandedAsync()
    {
        // Arrange
        var (kernel, serviceProvider, serviceSelector) = this.SetupKernel();

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables variables) =>
        {
            return $"Here is a payload '{variables["payload"]}' for " + variables.Input;
        },
       "function");

        var plan = new Plan("A plan with steps that have variables with a $ in them but not associated with an output");

        var planStep = new Plan(function);
        planStep.Parameters.Set("input", "Function input.");
        planStep.Parameters.Set("payload", @"{""prop"":""value"", ""$prop"": 3, ""prop2"": ""my name is $pop and $var""}");
        plan.AddSteps(planStep);
        plan.State.Set("var", "foobar");

        // Act
        var result = await plan.InvokeAsync(kernel);

        var expected = @"Here is a payload '{""prop"":""value"", ""$prop"": 3, ""prop2"": ""my name is $pop and foobar""}' for Function input.";

        // Assert
        Assert.Equal(expected, result.GetValue<string>());
    }

    [Fact]
    public async Task CanPlanStepsTriggerKernelEventsAsync()
    {
        List<KernelFunction> functions = new();

        // Arrange
        [KernelName("WritePoem")]
        static string Function2() => "Poem";
        functions.Add(KernelFunctionFactory.CreateFromMethod(Method(Function2)));

        [KernelName("SendEmail")]
        static string Function3() => "Sent Email";
        functions.Add(KernelFunctionFactory.CreateFromMethod(Method(Function3)));

        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal);
        plan.AddSteps(functions.ToArray());

        var expectedInvocations = 2;
        var sut = new KernelBuilder().Build();

        // 1 - Plan - Write poem and send email goal
        // 2 - Plan - Step 1 - WritePoem
        // 3 - Plan - Step 2 - WritePoem

        var invokingCalls = 0;
        var invokedCalls = 0;
        var invokingListFunctions = new List<KernelFunctionMetadata>();
        var invokedListFunctions = new List<KernelFunctionMetadata>();
        void FunctionInvoking(object? sender, FunctionInvokingEventArgs e)
        {
            invokingListFunctions.Add(e.Function.GetMetadata());
            invokingCalls++;
        }

        void FunctionInvoked(object? sender, FunctionInvokedEventArgs e)
        {
            invokedListFunctions.Add(e.Function.GetMetadata());
            invokedCalls++;
        }

        sut.FunctionInvoking += FunctionInvoking;
        sut.FunctionInvoked += FunctionInvoked;

        // Act
        var result = await plan.InvokeAsync(sut, "PlanInput");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedInvocations, invokingCalls);
        Assert.Equal(expectedInvocations, invokedCalls);

        // Expected invoking sequence
        Assert.Equal(invokingListFunctions[0].Name, functions[0].Name);
        Assert.Equal(invokingListFunctions[1].Name, functions[1].Name);

        // Expected invoked sequence
        Assert.Equal(invokedListFunctions[0].Name, functions[0].Name);
        Assert.Equal(invokedListFunctions[1].Name, functions[1].Name);
    }

    [Fact]
    public async Task PlanIsCancelledWhenInvokingHandlerTriggersCancelAsync()
    {
        // Arrange
        this.PrepareKernelAndPlan(out var sut, out var plan);

        var expectedInvokingHandlerInvocations = 1;
        var expectedInvokedHandlerInvocations = 0;
        var invokingCalls = 0;
        var invokedCalls = 0;
        var invokingListFunctions = new List<KernelFunctionMetadata>();
        var invokedListFunctions = new List<KernelFunctionMetadata>();

        void FunctionInvoking(object? sender, FunctionInvokingEventArgs e)
        {
            invokingListFunctions.Add(e.Function.GetMetadata());
            invokingCalls++;

            e.Cancel();
        }

        void FunctionInvoked(object? sender, FunctionInvokedEventArgs e)
        {
            invokedListFunctions.Add(e.Function.GetMetadata());
            invokedCalls++;
        }

        sut.FunctionInvoking += FunctionInvoking;
        sut.FunctionInvoked += FunctionInvoked;

        // Act
        var result = await plan.InvokeAsync(sut, "PlanInput");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingCalls);
        Assert.Equal(expectedInvokedHandlerInvocations, invokedCalls);

        // Expected invoking sequence
        Assert.Equal(invokingListFunctions[0].Name, plan.Steps[0].Name);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingListFunctions.Count);

        // Expected invoked sequence
        Assert.Equal(expectedInvokedHandlerInvocations, invokedListFunctions.Count);
    }

    [Fact]
    public async Task PlanStopsAtTheStepWhenInvokingHandlerTriggersCancelAsync()
    {
        // Arrange
        this.PrepareKernelAndPlan(out var sut, out var plan);

        var expectedInvokingHandlerInvocations = 1;
        var expectedInvokedHandlerInvocations = 0;
        var invokingCalls = 0;
        var invokedCalls = 0;
        var invokingListFunctions = new List<KernelFunctionMetadata>();
        var invokedListFunctions = new List<KernelFunctionMetadata>();

        void FunctionInvoking(object? sender, FunctionInvokingEventArgs e)
        {
            invokingListFunctions.Add(e.Function.GetMetadata());
            invokingCalls++;

            if (e.Function.GetMetadata().Name == "WritePoem")
            {
                e.Cancel();
            }
        }

        void FunctionInvoked(object? sender, FunctionInvokedEventArgs e)
        {
            invokedListFunctions.Add(e.Function.GetMetadata());
            invokedCalls++;
        }

        sut.FunctionInvoking += FunctionInvoking;
        sut.FunctionInvoked += FunctionInvoked;

        // Act
        var result = await plan.InvokeAsync(sut, "PlanInput");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingCalls);
        Assert.Equal(expectedInvokedHandlerInvocations, invokedCalls);

        // Expected invoking sequence
        Assert.Equal(invokingListFunctions[0].Name, plan.Steps[0].Name);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingListFunctions.Count);

        // Expected invoked sequence
        Assert.Equal(expectedInvokedHandlerInvocations, invokedListFunctions.Count);

        // Aborting at any step of a plan, will invalidate the full plan result
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task PlanStopsAtTheStepWhenInvokedHandlerTriggersCancelAsync()
    {
        // Arrange
        this.PrepareKernelAndPlan(out var sut, out var plan);

        var expectedInvokingHandlerInvocations = 1;
        var expectedInvokedHandlerInvocations = 1;
        var invokingCalls = 0;
        var invokedCalls = 0;
        var invokingListFunctions = new List<KernelFunctionMetadata>();
        var invokedListFunctions = new List<KernelFunctionMetadata>();

        void FunctionInvoking(object? sender, FunctionInvokingEventArgs e)
        {
            invokingListFunctions.Add(e.Function.GetMetadata());
            invokingCalls++;
        }

        void FunctionInvoked(object? sender, FunctionInvokedEventArgs e)
        {
            invokedListFunctions.Add(e.Function.GetMetadata());
            invokedCalls++;

            if (e.Function.GetMetadata().Name == "WritePoem")
            {
                e.Cancel();
            }
        }

        sut.FunctionInvoking += FunctionInvoking;
        sut.FunctionInvoked += FunctionInvoked;

        // Act
        var result = await plan.InvokeAsync(sut, "PlanInput");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingCalls);
        Assert.Equal(expectedInvokedHandlerInvocations, invokedCalls);

        // Expected invoking sequence
        Assert.Equal(invokingListFunctions[0].Name, plan.Steps[0].Name);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingListFunctions.Count);

        // Expected invoked sequence
        Assert.Equal(expectedInvokedHandlerInvocations, invokedListFunctions.Count);
        Assert.Equal(invokedListFunctions[0].Name, plan.Steps[0].Name);

        // Aborting in invoked of the first step will abort the result and
        // the plan will render no result as no step succeeded previously.
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task PlanStopsAtFinalStepWhenInvokedHandlerTriggersCancelAsync()
    {
        // Arrange
        this.PrepareKernelAndPlan(out var sut, out var plan);

        var expectedInvokingHandlerInvocations = 2;
        var expectedInvokedHandlerInvocations = 2;
        var invokingCalls = 0;
        var invokedCalls = 0;
        var invokingListFunctions = new List<KernelFunctionMetadata>();
        var invokedListFunctions = new List<KernelFunctionMetadata>();

        void FunctionInvoking(object? sender, FunctionInvokingEventArgs e)
        {
            invokingListFunctions.Add(e.Function.GetMetadata());
            invokingCalls++;
        }

        void FunctionInvoked(object? sender, FunctionInvokedEventArgs e)
        {
            invokedListFunctions.Add(e.Function.GetMetadata());
            invokedCalls++;

            if (e.Function.GetMetadata().Name == "SendEmail")
            {
                e.Cancel();
            }
        }

        sut.FunctionInvoking += FunctionInvoking;
        sut.FunctionInvoked += FunctionInvoked;

        // Act
        var result = await plan.InvokeAsync(sut, "PlanInput");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingCalls);
        Assert.Equal(expectedInvokedHandlerInvocations, invokedCalls);

        // Expected invoking sequence
        Assert.Equal(invokingListFunctions[0].Name, plan.Steps[0].Name);
        Assert.Equal(invokingListFunctions[1].Name, plan.Steps[1].Name);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingListFunctions.Count);

        // Expected invoked sequence
        Assert.Equal(expectedInvokedHandlerInvocations, invokedListFunctions.Count);
        Assert.Equal(invokedListFunctions[0].Name, plan.Steps[0].Name);
        Assert.Equal(invokedListFunctions[1].Name, plan.Steps[1].Name);

        // Aborting last step in invoked will stop the plan result
        // and return the previous succeeded step result value.
        Assert.Equal("WritePoem", result.GetValue<string>());
    }

    [Fact(Skip = "Skipping is currently not supported for plans")]
    public async Task PlapSkippingFirstStepShouldGiveSendStepResultAsync()
    {
        // Arrange
        this.PrepareKernelAndPlan(out var sut, out var plan);

        var expectedInvokingHandlerInvocations = 3;
        var expectedInvokedHandlerInvocations = 2;
        var invokingCalls = 0;
        var invokedCalls = 0;
        var invokingListFunctions = new List<KernelFunctionMetadata>();
        var invokedListFunctions = new List<KernelFunctionMetadata>();

        void FunctionInvoking(object? sender, FunctionInvokingEventArgs e)
        {
            invokingListFunctions.Add(e.Function.GetMetadata());
            invokingCalls++;

            if (e.Function.GetMetadata().Name == "WritePoem")
            {
                e.Skip();
            }
        }

        void FunctionInvoked(object? sender, FunctionInvokedEventArgs e)
        {
            invokedListFunctions.Add(e.Function.GetMetadata());
            invokedCalls++;
        }

        sut.FunctionInvoking += FunctionInvoking;
        sut.FunctionInvoked += FunctionInvoked;

        // Act
        var result = await plan.InvokeAsync(sut, "PlanInput");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingCalls);
        Assert.Equal(expectedInvokedHandlerInvocations, invokedCalls);

        // Expected invoking sequence
        Assert.Equal(invokingListFunctions[0].Name, plan.Name);
        Assert.Equal(invokingListFunctions[1].Name, plan.Steps[0].Name);
        Assert.Equal(invokingListFunctions[2].Name, plan.Steps[1].Name);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingListFunctions.Count);

        // Expected invoked sequence
        Assert.Equal(expectedInvokedHandlerInvocations, invokedListFunctions.Count);

        // Skipped the first step (will not trigger invoked for it)
        Assert.Equal(invokedListFunctions[0].Name, plan.Steps[1].Name);
        Assert.Equal("SendEmail", result.GetValue<string>());
    }

    [Fact]
    public async Task PlanStopsAtTheMiddleStepWhenHandlerTriggersInvokingCancelAsync()
    {
        // Arrange
        this.PrepareKernelAndPlan(out var sut, out var plan);

        var expectedInvokingHandlerInvocations = 2;
        var expectedInvokedHandlerInvocations = 1;
        var invokingCalls = 0;
        var invokedCalls = 0;
        var invokingListFunctions = new List<KernelFunctionMetadata>();
        var invokedListFunctions = new List<KernelFunctionMetadata>();

        void FunctionInvoking(object? sender, FunctionInvokingEventArgs e)
        {
            invokingListFunctions.Add(e.Function.GetMetadata());
            invokingCalls++;

            if (e.Function.GetMetadata().Name == "SendEmail")
            {
                e.Cancel();
            }
        }

        void FunctionInvoked(object? sender, FunctionInvokedEventArgs e)
        {
            invokedListFunctions.Add(e.Function.GetMetadata());
            invokedCalls++;
        }

        sut.FunctionInvoking += FunctionInvoking;
        sut.FunctionInvoked += FunctionInvoked;

        // Act
        var result = await plan.InvokeAsync(sut, "PlanInput");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingCalls);
        Assert.Equal(expectedInvokedHandlerInvocations, invokedCalls);

        // Expected invoking sequence
        Assert.Equal(invokingListFunctions[0].Name, plan.Steps[0].Name);
        Assert.Equal(invokingListFunctions[1].Name, plan.Steps[1].Name);
        Assert.Equal(expectedInvokingHandlerInvocations, invokingListFunctions.Count);

        // Expected invoked sequence
        Assert.Equal(expectedInvokedHandlerInvocations, invokedListFunctions.Count);

        // Cancelling the second step, don't block the triggering "invoked" for the first step.
        Assert.Equal(invokedListFunctions[0].Name, plan.Steps[0].Name);

        // Aborting one any step of a plan, will render the value of the last executed step
        Assert.Equal("WritePoem", result.GetValue<string>());
    }

    private void PrepareKernelAndPlan(out Kernel kernel, out Plan plan)
    {
        kernel = new KernelBuilder().Build();

        plan = new Plan("Write a poem or joke and send it in an e-mail to Kai.");
        plan.AddSteps(new[]
        {
            kernel.CreateFunctionFromMethod(() => "WritePoem", "WritePoem"),
            kernel.CreateFunctionFromMethod(() => "SendEmail", "SendEmail"),
        });

        // 1 - Plan - Write poem and send email goal
        // 2 - Plan - Step 1 - WritePoem
        // 3 - Plan - Step 2 - SendEmail
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private (Kernel kernel, Mock<IAIServiceProvider> serviceProviderMock, Mock<IAIServiceSelector> serviceSelectorMock) SetupKernel(IEnumerable<IKernelPlugin>? plugins = null)
    {
        var serviceProvider = new Mock<IAIServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        var kernel = new Kernel(serviceProvider.Object, plugins);

        return (kernel, serviceProvider, serviceSelector);
    }
}
