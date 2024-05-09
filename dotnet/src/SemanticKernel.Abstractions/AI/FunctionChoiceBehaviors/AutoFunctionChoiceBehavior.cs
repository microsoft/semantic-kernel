// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represent <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
/// This behavior allows the model to decide whether to call the functions and, if so, which ones to call.
/// </summary>
public sealed class AutoFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// The class alias. Used as a value for the discriminator property for polymorphic deserialization
    /// of function choice behavior specified in JSON and YAML prompts.
    /// </summary>
    public const string Alias = "auto";

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionChoiceBehavior"/> class.
    /// </summary>
    [JsonConstructor]
    public AutoFunctionChoiceBehavior()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions information.</param>
    public AutoFunctionChoiceBehavior(IEnumerable<KernelFunction> functions)
    {
        this.Functions = functions.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator));
    }

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
    /// Fully qualified names of subset of the <see cref="Kernel"/>'s plugins' functions information to provide to the model.
    /// </summary>
    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions { get; init; }

    /// <inheritdoc />
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
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

                    // Make sure that every function can be found in the kernel.
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
