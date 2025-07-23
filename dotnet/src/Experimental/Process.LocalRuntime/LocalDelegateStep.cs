// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel.Process;

internal class LocalDelegateStep : LocalStep
{
    private readonly KernelProcessDelegateStepInfo _delegateStep;

    public LocalDelegateStep(KernelProcessDelegateStepInfo stepInfo, Kernel kernel, string? parentProcessId = null)
        : base(stepInfo, kernel, parentProcessId)
    {
        this._delegateStep = stepInfo;
    }

    protected override ValueTask InitializeStepAsync()
    {
        this._stepInstance = new KernelDelegateProcessStep(this._delegateStep.StepFunction);

        var kernelPlugin = KernelPluginFactory.CreateFromObject(this._stepInstance, pluginName: this._stepInfo.State.Id);

        // Load the kernel functions
        foreach (KernelFunction f in kernelPlugin)
        {
            this._functions.Add(f.Name, f);
        }

        this._initialInputs = this.FindInputChannels(this._functions, logger: null, this.ExternalMessageChannel);
        this._inputs = this._initialInputs.ToDictionary(kvp => kvp.Key, kvp => kvp.Value?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));

#if !NETCOREAPP
        return new ValueTask();
#else
        return ValueTask.CompletedTask;
#endif
    }
}
