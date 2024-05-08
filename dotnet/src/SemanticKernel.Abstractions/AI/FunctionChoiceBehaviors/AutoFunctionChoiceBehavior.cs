// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

public sealed class AutoFunctionChoiceBehavior : FunctionChoiceBehavior
{
    internal const int DefaultMaximumAutoInvokeAttempts = 5;

    [JsonConstructor]
    public AutoFunctionChoiceBehavior()
    {
    }

    public AutoFunctionChoiceBehavior(IEnumerable<KernelFunction> functions)
    {
        this.Functions = functions.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator));
    }

    [JsonPropertyName("maximumAutoInvokeAttempts")]
    public int MaximumAutoInvokeAttempts { get; init; } = DefaultMaximumAutoInvokeAttempts;

    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions { get; init; }

    public override FunctionChoiceBehaviorConfiguration Configure(FunctionChoiceBehaviorContext context)
    {
        bool autoInvoke = this.MaximumAutoInvokeAttempts > 0;

        // If auto-invocation is specified, we need a kernel to be able to invoke the functions.
        // Lack of a kernel is fatal: we don't want to tell the model we can handle the functions
        // and then fail to do so, so we fail before we get to that point. This is an error
        // on the consumers behalf: if they specify auto-invocation with any functions, they must
        // specify the kernel and the kernel must contain those functions.
        if (autoInvoke && context.Kernel is null)
        {
            throw new KernelException("Auto-invocation in Auto mode is not supported when no kernel is provided.");
        }

        IList<KernelFunctionMetadata>? availableFunctions = null;

        if (context.Kernel is not null)
        {
            if (this.Functions is { } functionFQNs && functionFQNs.Any())
            {
                foreach (var functionFQN in functionFQNs)
                {
                    availableFunctions ??= new List<KernelFunctionMetadata>();

                    // Make sure that every enabled function can be found in the kernel.
                    Debug.Assert(context.Kernel is not null);

                    var name = FunctionName.Parse(functionFQN, FunctionNameSeparator);

                    if (!context.Kernel!.Plugins.TryGetFunction(name.PluginName, name.Name, out var function))
                    {
                        throw new KernelException($"The specified function {functionFQN} is not available in the kernel.");
                    }

                    availableFunctions.Add(function.Metadata);
                }
            }
            else
            {
                // Provide all functions from the kernel.
                var kernelFunctions = context.Kernel.Plugins.GetFunctionsMetadata();
                availableFunctions = kernelFunctions.Any() ? kernelFunctions : null;
            }
        }

        return new FunctionChoiceBehaviorConfiguration()
        {
            AvailableFunctions = availableFunctions,
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts
        };
    }
}
