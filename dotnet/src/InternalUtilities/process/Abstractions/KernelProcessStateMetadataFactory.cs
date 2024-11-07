﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process.Internal;
internal static class ProcessStateMetadataFactory
{
    /// <summary>
    /// Captures Kernel Process Step State into <see cref="KernelProcessStateMetadata"/>
    /// </summary>
    /// <returns><see cref="KernelProcessStateMetadata"/></returns>
    private static KernelProcessStepStateMetadata StepInfoToProcessStateMetadata(KernelProcessStepInfo stepInfo)
    {
        KernelProcessStepStateMetadata metadata = new()
        {
            Name = stepInfo.State.Name,
            Id = stepInfo.State.Id,
            VersionInfo = stepInfo.State.Version
        };

        if (stepInfo.InnerStepType.TryGetSubtypeOfStatefulStep(out var genericStateType) && genericStateType != null)
        {
            var userStateType = genericStateType.GetGenericArguments()[0];
            var stateOriginalType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);

            var innerState = stateOriginalType.GetProperty(nameof(KernelProcessStepState<object>.State))?.GetValue(stepInfo.State);
            if (innerState != null)
            {
                metadata.State = innerState;
            }
        }

        return metadata;
    }

    /// <summary>
    /// Captures Kernel Process State into <see cref="KernelProcessStateMetadata"/>
    /// </summary>
    /// <returns><see cref="KernelProcessStateMetadata"/></returns>
    public static KernelProcessStateMetadata KernelProcessToProcessStateMetadata(KernelProcess kernelProcess)
    {
        KernelProcessStateMetadata metadata = new()
        {
            Name = kernelProcess.State.Name,
            Id = kernelProcess.State.Id,
            VersionInfo = kernelProcess.State.Version,
            StepsState = [],
        };

        foreach (var step in kernelProcess.Steps)
        {
            KernelProcessStateMetadata stepEventMetadata = new();
            if (step is KernelProcess stepSubprocess)
            {
                metadata.StepsState.Add(step.State.Name, KernelProcessToProcessStateMetadata(stepSubprocess));
            }
            else
            {
                metadata.StepsState.Add(step.State.Name, StepInfoToProcessStateMetadata(step));
            }
        }

        return metadata;
    }

    public static KernelProcessStepStateMetadata ToProcessStateMetadata(this KernelProcessStepInfo stepInfo)
    {
        if (stepInfo is KernelProcess subprocess)
        {
            return KernelProcessToProcessStateMetadata(subprocess);
        }

        return StepInfoToProcessStateMetadata(stepInfo);
    }
}
