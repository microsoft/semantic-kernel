// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Models.Storage;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Defines operations for managing the storage of process step information, state, and events.
/// </summary>
public interface IProcessStepStorageOperations
{
    // For now step data is fetched by parent process only.
    // Task FetchStepDataAsync(KernelProcessStepInfo step);

    /// <summary>
    /// Retrieves detailed information about a specific process step: parentId, version, etc.
    /// </summary>
    /// <param name="stepInfo">The step for which information is to be retrieved. This parameter cannot be null.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains a <see cref="StorageStepInfo"/>
    /// object with the step details, or <see langword="null"/> if the step information is not available.</returns>
    Task<StorageStepInfo?> GetStepInfoAsync(KernelProcessStepInfo stepInfo);

    /// <summary>
    /// Saves detailed information about a specific process step, such as parentId, version, etc.
    /// </summary>
    /// <param name="stepInfo"></param>
    /// <returns></returns>
    Task<bool> SaveStepInfoAsync(KernelProcessStepInfo stepInfo);

    /// <summary>
    /// Retrieves the current state of a process step.
    /// </summary>
    /// <param name="stepInfo"></param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the current state of the specified
    /// step, or <see langword="null"/> if the step does not exist.</returns>
    Task<KernelProcessStepState?> GetStepStateAsync(KernelProcessStepInfo stepInfo);

    /// <summary>
    /// Saves the current state of a process step.
    /// </summary>
    /// <param name="stepInfo"></param>
    /// <returns></returns>
    Task<bool> SaveStepStateAsync(KernelProcessStepInfo stepInfo);

    /// <summary>
    /// Retrieves the events associated with a specific process step.
    /// </summary>
    /// <param name="stepInfo"></param>
    /// <returns></returns>
    Task<StorageStepEvents?> GetStepEventsAsync(KernelProcessStepInfo stepInfo);

    /// <summary>
    /// Saves the events associated with a specific process step.
    /// </summary>
    /// <param name="stepInfo"></param>
    /// <param name="edgeGroups"></param>
    /// <returns></returns>
    Task<bool> SaveStepEventsAsync(KernelProcessStepInfo stepInfo, Dictionary<string, Dictionary<string, object?>>? edgeGroups = null);
    // Fot now step data can be saved to storage only by parent process only.
    // This is to only save data to storage at the end of the process super step excecution.
    //Task<bool> SaveStepDataToStorageAsync(KernelProcessStepInfo step);
}
