// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

public sealed class RequiredFunctionChoiceBehavior : FunctionChoiceBehavior
{
    internal const int DefaultMaximumAutoInvokeAttempts = 5;

    internal const int DefaultMaximumUseAttempts = 1;

    [JsonConstructor]
    public RequiredFunctionChoiceBehavior()
    {
    }

    public RequiredFunctionChoiceBehavior(IEnumerable<KernelFunction> functions)
    {
        this.Functions = functions.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator));
    }

    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions { get; init; }

    [JsonPropertyName("maximumAutoInvokeAttempts")]
    public int MaximumAutoInvokeAttempts { get; init; } = DefaultMaximumAutoInvokeAttempts;

    [JsonPropertyName("maximumUseAttempts")]
    public int MaximumUseAttempts { get; init; } = DefaultMaximumUseAttempts;

    public override FunctionChoiceBehaviorConfiguration Configure(FunctionChoiceBehaviorContext context)
    {
        List<KernelFunctionMetadata>? requiredFunctions = null;

        if (this.Functions is { } functionFQNs && functionFQNs.Any())
        {
            bool autoInvoke = this.MaximumAutoInvokeAttempts > 0;

            // If auto-invocation is specified, we need a kernel to be able to invoke the functions.
            // Lack of a kernel is fatal: we don't want to tell the model we can handle the functions
            // and then fail to do so, so we fail before we get to that point. This is an error
            // on the consumers behalf: if they specify auto-invocation with any functions, they must
            // specify the kernel and the kernel must contain those functions.
            if (autoInvoke && context.Kernel is null)
            {
                throw new KernelException("Auto-invocation in Any mode is not supported when no kernel is provided.");
            }

            foreach (var functionFQN in functionFQNs)
            {
                requiredFunctions ??= [];

                // Make sure that every enabled function can be found in the kernel.
                Debug.Assert(context.Kernel is not null);

                var name = FunctionName.Parse(functionFQN, FunctionNameSeparator);

                // Make sure that the required functions can be found in the kernel.
                if (!context.Kernel!.Plugins.TryGetFunction(name.PluginName, name.Name, out var function))
                {
                    throw new KernelException($"The specified function {functionFQN} is not available in the kernel.");
                }

                requiredFunctions.Add(function.Metadata);
            }
        }

        return new FunctionChoiceBehaviorConfiguration()
        {
            RequiredFunctions = requiredFunctions,
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts,
            MaximumUseAttempts = this.MaximumUseAttempts
        };
    }
}
