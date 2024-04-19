// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.PromptTemplates.Prompty;
internal class PromptyKernelFunction : KernelFunction
{
    private readonly global::Prompty.Core.Prompty _prompty;
    public PromptyKernelFunction(
        global::Prompty.Core.Prompty prompty,
        PromptTemplateConfig promptConfig)
        : base(prompty.Name, null, prompty.Description, promptConfig.GetKernelParametersMetadata(), promptConfig.GetKernelReturnParameterMetadata(), promptConfig.ExecutionSettings)
    {
        this._prompty = prompty;
    }
    public override KernelFunction Clone(string pluginName)
    {
        throw new NotImplementedException();
    }

    protected override ValueTask<FunctionResult> InvokeCoreAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    protected override IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }
}
