// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Models.Storage;

namespace Microsoft.SemanticKernel;

public interface IProcessStorageOperations
{
    Task<bool> InitializeAsync();
    Task<bool> CloseAsync();
    Task FetchProcessDataAsync(KernelProcess process);
    Task<StorageProcessInfo?> GetProcessInfoAsync(KernelProcess process);
    Task<bool> SaveProcessInfoAsync(KernelProcess process);
    Task<bool> SaveProcessEventsAsync(KernelProcess process, List<KernelProcessEvent>? pendingExternalEvents = null);
    Task<bool> SaveProcessDataToStorageAsync(KernelProcess process);

    // Step related operations to be applied to process children steps only
    Task FetchStepDataAsync(KernelProcessStepInfo step);
    Task<bool> SaveStepDataToStorageAsync(KernelProcessStepInfo step);
}
