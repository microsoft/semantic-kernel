// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder class for defining targets to listen for in a process.
/// </summary>
[Experimental("SKEXP0081")]
public class FoundryListenForTargetBuilder
{
    private readonly ListenForTargetBuilder _listenForTargetBuilder;

    internal FoundryListenForTargetBuilder(ListenForTargetBuilder listenForTargetBuilder)
    {
        this._listenForTargetBuilder = listenForTargetBuilder;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ListenForTargetBuilder"/> class.
    /// </summary>
    /// <param name="messageSources">The list of message sources.</param>
    /// <param name="processBuilder">The process builder.</param>
    /// <param name="edgeGroup">The group ID for the message sources.</param>
    public FoundryListenForTargetBuilder(List<MessageSourceBuilder> messageSources, ProcessBuilder processBuilder, KernelProcessEdgeGroupBuilder? edgeGroup = null)
    {
        this._listenForTargetBuilder = new ListenForTargetBuilder(messageSources, processBuilder, edgeGroup);
    }

    /// <summary>
    /// Signals that the output of the source step should be sent to the specified target when the associated event fires.
    /// </summary>
    /// <param name="target">The output target.</param>
    /// <param name="thread"> The thread to send the event to.</param>
    /// <param name="inputs"> The inputs to the target.</param>
    /// <param name="messagesIn"> The messages to be sent to the target.</param>
    /// <returns>A fresh builder instance for fluid definition</returns>
    public ProcessStepEdgeBuilder SendEventTo<TProcessState>(ProcessAgentBuilder<TProcessState> target, string? thread = null, Dictionary<string, string>? inputs = null, List<string>? messagesIn = null) where TProcessState : class, new()
    {
        return this._listenForTargetBuilder.SendEventTo_Internal(new ProcessAgentInvokeTargetBuilder(target, thread, messagesIn ?? [], inputs ?? []));
    }

    /// <summary>
    /// Signals that the specified event should be emitted.
    /// </summary>
    /// <param name="eventName"></param>
    /// <param name="payload"></param>
    /// <returns></returns>
    public FoundryListenForTargetBuilder EmitEvent(string eventName, Dictionary<string, string>? payload = null)
    {
        return new(this._listenForTargetBuilder.EmitEvent(eventName, payload));
    }

    /// <summary>
    /// Signals that the specified state variable should be updated in the process state.
    /// </summary>
    /// <param name="path"></param>
    /// <param name="operation"></param>
    /// <param name="value"></param>
    /// <returns></returns>
    public FoundryListenForTargetBuilder UpdateProcessState(string path, StateUpdateOperations operation, object? value)
    {
        return new(this._listenForTargetBuilder.UpdateProcessState(path, operation, value));
    }

    /// <summary>
    /// Signals that the process should be stopped.
    /// </summary>
    public void StopProcess(string? thread = null, Dictionary<string, string>? inputs = null, List<string>? messagesIn = null)
    {
        var target = new ProcessAgentInvokeTargetBuilder(EndStep.Instance, thread, messagesIn ?? [], inputs ?? []);
        this._listenForTargetBuilder.SendEventTo_Internal(target);
    }
}
