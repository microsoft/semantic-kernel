// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represent <see cref="FunctionChoiceBehavior"/> that provides a subset of the <see cref="Kernel"/>'s plugins' function information to the model.
/// This behavior forces the model to always call one or more functions. The model will then select which function(s) to call.
/// </summary>
public sealed class RequiredFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// The class alias. Used as a value for the discriminator property for polymorphic deserialization
    /// of function choice behavior specified in JSON and YAML prompts.
    /// </summary>
    public const string Alias = "required";

    /// <summary>
    /// Initializes a new instance of the <see cref="RequiredFunctionChoiceBehavior"/> class.
    /// </summary>
    [JsonConstructor]
    public RequiredFunctionChoiceBehavior()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="RequiredFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions information.</param>
    public RequiredFunctionChoiceBehavior(IEnumerable<KernelFunction> functions)
    {
        this.Functions = functions.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator));
    }

    /// <summary>
    /// Fully qualified names of subset of the <see cref="Kernel"/>'s plugins' functions information to provide to the model.
    /// </summary>
    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions { get; init; }

    /// <summary>
    /// The maximum number of function auto-invokes that can be made in a single user request.
    /// </summary>
    /// <remarks>
    /// After this number of iterations as part of a single user request is reached, auto-invocation
    /// will be disabled. This is a safeguard against possible runaway execution if the model routinely re-requests
    /// the same function over and over. To disable auto invocation, this can be set to 0.
    /// </remarks>
    [JsonPropertyName("maximumAutoInvokeAttempts")]
    public int MaximumAutoInvokeAttempts { get; init; } = DefaultMaximumAutoInvokeAttempts;

    /// <summary>
    /// Number of requests that are part of a single user interaction that should include this functions in the request.
    /// </summary>
    /// <remarks>
    /// This should be greater than or equal to <see cref="MaximumAutoInvokeAttempts"/>.
    /// Once this limit is reached, the functions will no longer be included in subsequent requests that are part of the user operation, e.g.
    /// if this is 1, the first request will include the functions, but the subsequent response sending back the functions' result
    /// will not include the functions for further use.
    /// </remarks>
    [JsonPropertyName("maximumUseAttempts")]
    public int MaximumUseAttempts { get; init; } = 1;

    /// <inheritdoc />
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
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
