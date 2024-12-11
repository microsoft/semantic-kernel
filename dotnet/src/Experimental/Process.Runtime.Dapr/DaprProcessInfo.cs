// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.Serialization;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Interfaces;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Dapr Process.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessState))]
[KnownType(typeof(KernelProcessMapState))]
[KnownType(typeof(KernelProcessStepState))]
[KnownType(typeof(KernelProcessStepState<>))]
public sealed record DaprProcessInfo : DaprStepInfo
{
    /// <summary>
    /// The collection of Steps in the Process.
    /// </summary>
    public required IList<DaprStepInfo> Steps { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcess"/> class from this instance of <see cref="DaprProcessInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    /// <exception cref="KernelException"></exception>
    public KernelProcess ToKernelProcess()
    {
        var processStepInfo = this.ToKernelProcessStepInfo();
        if (this.State is not KernelProcessState state)
        {
            throw new KernelException($"Unable to read state from process with name '{this.State.Name}' and Id '{this.State.Id}'.");
        }

        List<KernelProcessStepInfo> steps = [];
        foreach (var step in this.Steps)
        {
            if (step is DaprProcessInfo processStep)
            {
                steps.Add(processStep.ToKernelProcess());
            }
            else if (step is DaprMapInfo mapStep)
            {
                steps.Add(mapStep.ToKernelProcessMap());
            }
            else
            {
                steps.Add(step.ToKernelProcessStepInfo());
            }
        }

        return new KernelProcess(state, steps, this.Edges);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DaprProcessInfo"/> class from an instance of <see cref="KernelProcess"/>.
    /// </summary>
    /// <param name="kernelProcess">The <see cref="KernelProcess"/> used to build the <see cref="DaprProcessInfo"/></param>
    /// <returns>An instance of <see cref="DaprProcessInfo"/></returns>
    public static DaprProcessInfo FromKernelProcess(KernelProcess kernelProcess)
    {
        Verify.NotNull(kernelProcess);

        var processDaprEvents = ConvertToStepPubsubData(kernelProcess.EventsSubscriber?.GetLinkedDaprPublishEventsInfoBySource(kernelProcess.State.Id!));
        DaprStepInfo daprStepInfo = DaprStepInfo.FromKernelStepInfo(kernelProcess, []);
        List<DaprStepInfo> daprSteps = [];

        foreach (var step in kernelProcess.Steps)
        {
            var externalEvents = kernelProcess.EventsSubscriber?.GetLinkedDaprPublishEventsInfoBySource(step.State.Id!);
            var daprEvents = ConvertToStepPubsubData(externalEvents);

            if (step is KernelProcess processStep)
            {
                daprSteps.Add(DaprProcessInfo.FromKernelProcess(processStep));
            }
            else if (step is KernelProcessMap mapStep)
            {
                daprSteps.Add(DaprMapInfo.FromKernelProcessMap(mapStep));
            }
            else
            {
                daprSteps.Add(DaprStepInfo.FromKernelStepInfo(step, daprEvents));
            }
        }

        return new DaprProcessInfo
        {
            InnerStepDotnetType = daprStepInfo.InnerStepDotnetType,
            State = daprStepInfo.State,
            Edges = daprStepInfo.Edges,
            Steps = daprSteps,
            ExternalEventsMap = processDaprEvents,
        };
    }

    private static Dictionary<string, DaprPubsubEventData> ConvertToStepPubsubData(IDictionary<string, IDaprPubsubEventInfo>? daprEvents)
    {
        if (daprEvents == null)
        {
            return [];
        }

        return daprEvents.ToDictionary(e => e.Key, e => new DaprPubsubEventData()
        {
            ProcessEventName = e.Value.EventName,
            PubsubName = e.Value.DaprPubsub!,
            TopicName = e.Value.DaprTopic!,
        });
    }
}
