// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process.Internal;
internal static class ProcessStateMetadataFactory
{
    /// <summary>
    /// Captures Kernel Process Step State into <see cref="KernelProcessStateMetadata"/>
    /// </summary>
    /// <returns><see cref="KernelProcessStateMetadata"/></returns>
    private static KernelProcessStateMetadata StepInfoToProcessStateMetadata(KernelProcessStepInfo stepInfo)
    {
        KernelProcessStateMetadata metadata = new()
        {
            Name = stepInfo.State.Name,
            Id = stepInfo.State.Id,
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
            StepsState = [],
        };

        foreach (var step in kernelProcess.Steps)
        {
            KernelProcessStateMetadata stepEventMetadata = new();
            if (step is KernelProcess stepSubprocess)
            {
                stepEventMetadata = KernelProcessToProcessStateMetadata(stepSubprocess);
            }
            else
            {
                stepEventMetadata = StepInfoToProcessStateMetadata(step);
            }

            metadata.StepsState.Add(step.State.Name, stepEventMetadata);
        }

        return metadata;
    }

    public static KernelProcessStateMetadata ToProcessStateMetadata(this KernelProcessStepInfo stepInfo)
    {
        if (stepInfo is KernelProcess subprocess)
        {
            return KernelProcessToProcessStateMetadata(subprocess);
        }

        return StepInfoToProcessStateMetadata(stepInfo);
    }
}
