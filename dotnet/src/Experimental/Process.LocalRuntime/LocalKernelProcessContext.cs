// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides context and actions on a process that is running locally.
/// </summary>
public class LocalKernelProcessContext
{
    private readonly string _processId;
    private readonly LocalProcess _localProcess;
    private Task? _processTask;
    private readonly Kernel _kernel;

    internal LocalKernelProcessContext(KernelProcess process, Kernel kernel)
    {
        Verify.NotNull(process);
        Verify.NotNullOrWhiteSpace(process.State?.Name);
        Verify.NotNull(kernel);

        this._kernel = kernel;
        this._localProcess = new LocalProcess(
            process,
            kernel: kernel,
            parentProcessId: null,
            loggerFactory: null);

        this._processId = this._localProcess.Id;
    }

    internal void Start(KernelProcessEvent initialEvent, Kernel? kernel = null)
    {
        this._processTask = this._localProcess.ExecuteAsync(kernel, initialEvent, 100);
    }
}
