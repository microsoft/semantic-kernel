// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithDapr.Processes;

public interface IProcessManager
{
    Task<DaprKernelProcessContext> StartProcessAsync(string processId);
    DaprKernelProcessContext? GetProcessContext(string processId);
}
