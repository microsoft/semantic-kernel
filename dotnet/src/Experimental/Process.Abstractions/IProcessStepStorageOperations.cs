// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Models.Storage;

namespace Microsoft.SemanticKernel;

public interface IProcessStepStorageOperations
{
    // For now step data is fetched by parent process only.
    // Task FetchStepDataAsync(KernelProcessStepInfo step);
    Task<StorageStepInfo?> GetStepInfoAsync(KernelProcessStepInfo step);
    Task<bool> SaveStepInfoAsync(KernelProcessStepInfo step);
    Task<KernelProcessStepState?> GetStepStateAsync(KernelProcessStepInfo step);
    Task<bool> SaveStepStateAsync(KernelProcessStepInfo step);
    Task<StorageStepEvents?> GetStepEventsAsync(KernelProcessStepInfo step);
    Task<bool> SaveStepEventsAsync(KernelProcessStepInfo step, Dictionary<string, Dictionary<string, object?>>? edgeGroups = null);
    // Fot now step data can be saved to storage only by parent process only.
    // This is to only save data to storage at the end of the process super step excecution.
    //Task<bool> SaveStepDataToStorageAsync(KernelProcessStepInfo step);
}
