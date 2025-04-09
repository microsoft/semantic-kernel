// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Runtime.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.IntegrationTests;

#pragma warning disable CS1591 // Missing XML comment for publicly visible type or member

/// <summary>
/// Kick off step for the process.
/// </summary>
public sealed class KickoffStep : KernelProcessStep
{
    public static class Functions
    {
        public const string KickOff = nameof(KickOff);
    }

    [KernelFunction(Functions.KickOff)]
    public async ValueTask PrintWelcomeMessageAsync(KernelProcessStepContext context)
    {
        await context.EmitEventAsync(new() { Id = CommonEvents.StartARequested, Data = "Get Going A" });
        await context.EmitEventAsync(new() { Id = CommonEvents.StartBRequested, Data = "Get Going B" });
    }
}

/// <summary>
/// A step in the process.
/// </summary>
public sealed class AStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context)
    {
        await Task.Delay(TimeSpan.FromSeconds(1));
        await context.EmitEventAsync(new() { Id = CommonEvents.AStepDone, Data = "I did A" });
    }
}

/// <summary>
/// A step in the process.
/// </summary>
public sealed class BStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context)
    {
        await Task.Delay(TimeSpan.FromSeconds(2));
        await context.EmitEventAsync(new() { Id = CommonEvents.BStepDone, Data = "I did B" });
    }
}

/// <summary>
/// A step in the process.
/// </summary>
public sealed class CStep : KernelProcessStep<CStepState>
{
    private CStepState? _state = new();

    public override ValueTask ActivateAsync(KernelProcessStepState<CStepState> state)
    {
        this._state = state.State;
        return base.ActivateAsync(state);
    }

    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context, string astepdata, string bstepdata)
    {
        this._state!.CurrentCycle++;
        if (this._state.CurrentCycle == 3)
        {
            // Exit the processes
            await context.EmitEventAsync(new() { Id = CommonEvents.ExitRequested });
            return;
        }

        // Cycle back to the start
        await context.EmitEventAsync(new() { Id = CommonEvents.CStepDone });
    }
}

/// <summary>
/// A state object for the CStep.
/// </summary>
[DataContract]
public sealed record CStepState
{
    [DataMember]
    public int CurrentCycle { get; set; }
}

/// <summary>
/// Common Events used in the process.
/// </summary>
public static class CommonEvents
{
    public const string UserInputReceived = nameof(UserInputReceived);
    public const string CompletionResponseGenerated = nameof(CompletionResponseGenerated);
    public const string WelcomeDone = nameof(WelcomeDone);
    public const string AStepDone = nameof(AStepDone);
    public const string BStepDone = nameof(BStepDone);
    public const string CStepDone = nameof(CStepDone);
    public const string StartARequested = nameof(StartARequested);
    public const string StartBRequested = nameof(StartBRequested);
    public const string ExitRequested = nameof(ExitRequested);
    public const string StartProcess = nameof(StartProcess);
}

/// <summary>
/// A step that repeats its input. Emits data internally AND publicly
/// </summary>
public sealed class RepeatStep : KernelProcessStep<StepState>
{
    private StepState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<StepState> state)
    {
        this._state = state.State;
        return default;
    }

    [KernelFunction]
    public async Task RepeatAsync(string message, KernelProcessStepContext context, int count = 2)
    {
        var output = string.Join(" ", Enumerable.Repeat(message, count));
        Console.WriteLine($"[REPEAT] {output}");
        this._state!.LastMessage = output;

        // Emit the OnReady event with a public visibility and an internal visibility to aid in testing
        await context.EmitEventAsync(new() { Id = ProcessTestsEvents.OutputReadyPublic, Data = output, Visibility = KernelProcessEventVisibility.Public });
        await context.EmitEventAsync(new() { Id = ProcessTestsEvents.OutputReadyInternal, Data = output, Visibility = KernelProcessEventVisibility.Internal });
    }
}

/// <summary>
/// A step that emits the input received internally OR publicly.
/// </summary>
public sealed class EmitterStep : KernelProcessStep<StepState>
{
    public const string EventId = "Next";
    public const string PublicEventId = "PublicNext";
    public const string InputEvent = "OnInput";
    public const string Name = nameof(EmitterStep);

    public const string InternalEventFunction = "SomeInternalFunctionName";
    public const string PublicEventFunction = "SomePublicFunctionName";
    public const string DualInputPublicEventFunction = "SomeDualInputPublicEventFunctionName";

    private readonly int _sleepDurationMs = 150;

    private StepState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<StepState> state)
    {
        this._state = state.State;
        return default;
    }

    [KernelFunction(InternalEventFunction)]
    public async Task InternalTestFunctionAsync(KernelProcessStepContext context, string data)
    {
        Thread.Sleep(this._sleepDurationMs);

        Console.WriteLine($"[EMIT_INTERNAL] {data}");
        this._state!.LastMessage = data;
        await context.EmitEventAsync(new() { Id = EventId, Data = data });
    }

    [KernelFunction(PublicEventFunction)]
    public async Task PublicTestFunctionAsync(KernelProcessStepContext context, string data)
    {
        Thread.Sleep(this._sleepDurationMs);

        Console.WriteLine($"[EMIT_PUBLIC] {data}");
        this._state!.LastMessage = data;
        await context.EmitEventAsync(new() { Id = PublicEventId, Data = data, Visibility = KernelProcessEventVisibility.Public });
    }

    [KernelFunction(DualInputPublicEventFunction)]
    public async Task DualInputPublicTestFunctionAsync(KernelProcessStepContext context, string firstInput, string secondInput)
    {
        Thread.Sleep(this._sleepDurationMs);

        string outputText = $"{firstInput}-{secondInput}";
        Console.WriteLine($"[EMIT_PUBLIC_DUAL] {outputText}");
        this._state!.LastMessage = outputText;
        await context.EmitEventAsync(new() { Id = ProcessTestsEvents.OutputReadyPublic, Data = outputText, Visibility = KernelProcessEventVisibility.Public });
    }
}

/// <summary>
/// A step that emits a startProcess event
/// </summary>
public sealed class StartStep : KernelProcessStep
{
    [KernelFunction]
    public async Task SendStartMessageAsync(KernelProcessStepContext context, string text)
    {
        Console.WriteLine($"[START] {text}");
        await context.EmitEventAsync(new()
        {
            Id = ProcessTestsEvents.StartProcess,
            Data = text,
            Visibility = KernelProcessEventVisibility.Public
        });
    }
}

/// <summary>
/// A step that combines string inputs received.
/// </summary>
public sealed class FanInStep : KernelProcessStep<StepState>
{
    private StepState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<StepState> state)
    {
        this._state = state.State;
        return default;
    }

    [KernelFunction]
    public async Task EmitCombinedMessageAsync(KernelProcessStepContext context, string firstInput, string secondInput)
    {
        var output = $"{firstInput}-{secondInput}";
        Console.WriteLine($"[EMIT_COMBINED] {output}");
        this._state!.LastMessage = output;

        await context.EmitEventAsync(new()
        {
            Id = ProcessTestsEvents.OutputReadyInternal,
            Data = output,
            Visibility = KernelProcessEventVisibility.Internal
        });
        await context.EmitEventAsync(new()
        {
            Id = ProcessTestsEvents.OutputReadyPublic,
            Data = output,
            Visibility = KernelProcessEventVisibility.Public
        });
    }
}

/// <summary>
/// A step that conditionally throws an exception.
/// </summary>
public sealed class ErrorStep : KernelProcessStep<StepState>
{
    private StepState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<StepState> state)
    {
        this._state = state.State;
        return default;
    }

    [KernelFunction]
    public async Task ErrorWhenTrueAsync(KernelProcessStepContext context, bool shouldError)
    {
        this._state!.InvocationCount++;

        if (shouldError)
        {
            throw new InvalidOperationException("This is an error");
        }

        await context.EmitEventAsync(new()
        {
            Id = ProcessTestsEvents.ErrorStepSuccess,
            Data = null,
            Visibility = KernelProcessEventVisibility.Internal
        });
    }
}

/// <summary>
/// A step that reports an error sent to it by logging it to the console.
/// </summary>
public sealed class ReportStep : KernelProcessStep<StepState>
{
    private StepState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<StepState> state)
    {
        this._state = state.State;
        return default;
    }

    [KernelFunction]
    public Task ReportError(KernelProcessStepContext context, object error)
    {
        this._state!.InvocationCount++;
        Console.WriteLine(error.ToString());
        return Task.CompletedTask;
    }
}

/// <summary>
/// The state object for the repeat and fanIn step.
/// </summary>
[DataContract]
public sealed record StepState
{
    [DataMember]
    public string? LastMessage { get; set; }

    [DataMember]
    public int InvocationCount { get; set; }
}

/// <summary>
/// A class that defines the events that can be emitted by the chat bot process. This is
/// not required but used to ensure that the event names are consistent.
/// </summary>
public static class ProcessTestsEvents
{
    public const string StartProcess = "StartProcess";
    public const string StartInnerProcess = "StartInnerProcess";
    public const string OutputReadyPublic = "OutputReadyPublic";
    public const string OutputReadyInternal = "OutputReadyInternal";
    public const string ErrorStepSuccess = "ErrorStepSuccess";
}

#pragma warning restore CS1591 // Missing XML comment for publicly visible type or member
