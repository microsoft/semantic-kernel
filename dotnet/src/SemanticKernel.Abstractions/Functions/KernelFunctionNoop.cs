// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a kernel function that performs no operation.
/// </summary>
[RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
[RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
internal sealed class KernelFunctionNoop : KernelFunction
{
    /// <summary>
    /// Creates a new instance of the <see cref="KernelFunctionNoop"/> class.
    /// </summary>
    /// <param name="executionSettings">Option: Prompt execution settings.</param>
    internal KernelFunctionNoop(IReadOnlyDictionary<string, PromptExecutionSettings>? executionSettings) :
        base($"Function_{Guid.NewGuid():N}", string.Empty, [], null, executionSettings?.ToDictionary(static kv => kv.Key, static kv => kv.Value))
    {
    }

    /// <inheritdoc/>
    public override KernelFunction Clone(string pluginName)
    {
        Dictionary<string, PromptExecutionSettings>? executionSettings = this.ExecutionSettings?.ToDictionary(kv => kv.Key, kv => kv.Value);
        return new KernelFunctionNoop(executionSettings);
    }

    /// <inheritdoc/>
    protected override ValueTask<FunctionResult> InvokeCoreAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        return new(new FunctionResult(this));
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        return AsyncEnumerable.Empty<TResult>();
    }
}
