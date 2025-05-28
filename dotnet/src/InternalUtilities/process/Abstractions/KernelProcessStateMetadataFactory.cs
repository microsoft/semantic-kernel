// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process.Internal;

internal static class ProcessStateMetadataFactory
{
    /// <summary>
    /// Captures Kernel Process State into <see cref="KernelProcessStateMetadata"/>
    /// </summary>
    /// <returns><see cref="KernelProcessStateMetadata"/></returns>
    public static KernelProcessStateMetadata KernelProcessToProcessStateMetadata(KernelProcess kernelProcess)
    {
        KernelProcessStateMetadata metadata = new()
        {
            Name = kernelProcess.State.StepId,
            Id = kernelProcess.State.RunId,
            VersionInfo = kernelProcess.State.Version,
            StepsState = [],
        };

        foreach (KernelProcessStepInfo step in kernelProcess.Steps)
        {
            metadata.StepsState.Add(step.State.StepId, step.ToProcessStateMetadata());
        }

        return metadata;
    }

    public static KernelProcessStepStateMetadata ToProcessStateMetadata(this KernelProcessStepInfo stepInfo)
    {
        if (stepInfo is KernelProcess subprocess)
        {
            return KernelProcessToProcessStateMetadata(subprocess);
        }
        else if (stepInfo is KernelProcessMap stepMap)
        {
            return KernelProcessMapToProcessStateMetadata(stepMap);
        }
        else if (stepInfo is KernelProcessProxy stepProxy)
        {
            return KernelProcessProxyToProcessStateMetadata(stepProxy);
        }

        return StepInfoToProcessStateMetadata(stepInfo);
    }

    private static KernelProcessMapStateMetadata KernelProcessMapToProcessStateMetadata(KernelProcessMap stepMap)
    {
        return
            new()
            {
                Name = stepMap.State.StepId,
                Id = stepMap.State.RunId,
                VersionInfo = stepMap.State.Version,
                OperationState = ToProcessStateMetadata(stepMap.Operation),
            };
    }

    private static KernelProcessProxyStateMetadata KernelProcessProxyToProcessStateMetadata(KernelProcessProxy stepProxy)
    {
        return new()
        {
            Name = stepProxy.State.StepId,
            Id = stepProxy.State.RunId,
            VersionInfo = stepProxy.State.Version,
            PublishTopics = stepProxy.ProxyMetadata?.PublishTopics ?? [],
            EventMetadata = stepProxy.ProxyMetadata?.EventMetadata ?? [],
        };
    }

    /// <summary>
    /// Captures Kernel Process Step State into <see cref="KernelProcessStateMetadata"/>
    /// </summary>
    /// <returns><see cref="KernelProcessStateMetadata"/></returns>
    private static KernelProcessStepStateMetadata StepInfoToProcessStateMetadata(KernelProcessStepInfo stepInfo)
    {
        KernelProcessStepStateMetadata metadata = new()
        {
            Name = stepInfo.State.StepId,
            Id = stepInfo.State.RunId,
            VersionInfo = stepInfo.State.Version
        };

        if (stepInfo.InnerStepType.TryGetSubtypeOfStatefulStep(out Type? genericStateType) && genericStateType != null)
        {
            Type userStateType = genericStateType.GetGenericArguments()[0];
            Type stateOriginalType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);

            object? innerState = stateOriginalType.GetProperty(nameof(KernelProcessStepState<object>.State))?.GetValue(stepInfo.State);
            if (innerState != null)
            {
                metadata.State = innerState;
            }
        }

        return metadata;
    }
}
