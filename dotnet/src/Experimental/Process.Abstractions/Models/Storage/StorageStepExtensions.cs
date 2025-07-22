// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel.Process.Models.Storage;
/// <summary>
/// Extension methods for converting between StorageStepState and KernelProcessStepStateMetadata.
/// </summary>
public static class StorageStepExtensions
{
    public static StorageStepInfo ToStorageStepInfo(this KernelProcessStepInfo step)
    {
        return new StorageStepInfo
        {
            StepName = step.StepId!,
            InstanceId = step.RunId!,
            ParentId = step.ParentId!,
            // There should be a distinction between stepName version and stepState version
            // A stepName could be compatible with a previous stepState version
            Version = step.State.Version,
        };
    }

    public static KernelProcessStepState ToKernelProcessStepState(this StorageStepData storageData)
    {
        var stepState = new KernelProcessStepState(stepId: storageData.StepInfo.StepName, version: storageData.StepInfo.Version, runId: storageData.InstanceId)
        {
            ParentId = storageData.StepInfo.ParentId,
        };

        if (storageData.StepState != null && !string.IsNullOrEmpty(storageData.StepState.StateType))
        {
            var userStateType = Type.GetType(storageData.StepState.StateType);
            if (userStateType != null && storageData.StepState.State != null)
            {
                var stateType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);
                stepState = (KernelProcessStepState?)Activator.CreateInstance(stateType, stepState);
                stateType.GetProperty(nameof(KernelProcessStepState<object>.State))?.SetValue(stepState, storageData.StepState.State.ToObject());
            }
        }

        return stepState;
    }

    public static StorageStepState? ToStorageStepState(this KernelProcessStepInfo step)
    {
        object? stepState = null;
        var stateType = step.State.GetType();
        if (stateType.IsGenericType)
        {
            // it is a step with a custom state
            stepState = stateType.GetProperty(nameof(KernelProcessStepState<object>.State))?.GetValue(step.State);

            return new StorageStepState
            {
                State = KernelProcessEventData.FromObject(stepState),
                StateType = stateType.GetGenericArguments()[0].AssemblyQualifiedName!
            };
        }

        return null;
    }

    public static StorageStepEvents ToStorageStepEvents(this KernelProcessStepInfo step, Dictionary<string, Dictionary<string, object?>?>? edgeGroups = null)
    {
        return new StorageStepEvents
        {
            EdgesData = edgeGroups?.PackStepEdgesValues()
        };
    }

 
}
