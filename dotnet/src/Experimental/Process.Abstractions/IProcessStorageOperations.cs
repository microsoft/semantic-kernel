// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Models.Storage;

namespace Microsoft.SemanticKernel;

internal interface IProcessStorageOperations
{
    /// <summary>
    /// Initializes the storage connection to be used by the process.
    /// </summary>
    /// <returns></returns>
    Task<bool> InitializeAsync();
    /// <summary>
    /// Closes storage connection and cleans up resources.
    /// </summary>
    /// <returns></returns>
    Task<bool> CloseAsync();
    /// <summary>
    /// Fetches from storage the process data for a specific process.
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    Task FetchProcessDataAsync(KernelProcess process);
    /// <summary>
    /// Get the process information already retrieved from storage, including parentId, version, mapping of steps and running ids.
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    Task<StorageProcessInfo?> GetProcessInfoAsync(KernelProcess process);
    /// <summary>
    /// Saves the process information to storage, including parentId, version, mapping of steps and running ids.
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    Task<bool> SaveProcessInfoAsync(KernelProcess process);

    /// <summary>
    /// Retrieves a list of external events associated with the specified kernel process.
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    Task<List<KernelProcessEvent>?> GetProcessExternalEventsAsync(KernelProcess process);

    /// <summary>
    /// Save process events to storage, including pending external events.
    /// </summary>
    /// <param name="process"></param>
    /// <param name="pendingExternalEvents"></param>
    /// <returns></returns>
    Task<bool> SaveProcessEventsAsync(KernelProcess process, List<KernelProcessEvent>? pendingExternalEvents = null);

    /// <summary>
    /// Retrieve process shared variables
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    Task<Dictionary<string, object?>?> GetProcessStateVariablesAsync(KernelProcess process);

    /// <summary>
    /// Save process state related components
    /// </summary>
    /// <param name="process"></param>
    /// <param name="sharedVariables"></param>
    /// <returns></returns>
    Task<bool> SaveProcessStateAsync(KernelProcess process, Dictionary<string, object> sharedVariables);

    /// <summary>
    /// Saves all process related data to storage, including process info, events, and step data.
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    Task<bool> SaveProcessDataToStorageAsync(KernelProcess process);

    // Step related operations to be applied to process children steps only

    /// <summary>
    /// Fetches from storage the step data for a specific process step.
    /// </summary>
    /// <param name="stepInfo"></param>
    /// <returns></returns>
    Task FetchStepDataAsync(KernelProcessStepInfo stepInfo);

    /// <summary>
    /// Saves the step data to storage.
    /// </summary>
    /// <param name="stepInfo"></param>
    /// <returns></returns>
    Task<bool> SaveStepDataToStorageAsync(KernelProcessStepInfo stepInfo);
}
