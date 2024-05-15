// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represent <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
/// This behavior forces the model to always call one or more functions. The model will then select which function(s) to call.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class RequiredFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// List of the functions that the model can choose from.
    /// </summary>
    private readonly IEnumerable<KernelFunction>? _functions;

    /// <summary>
    /// This class type discriminator used for polymorphic deserialization of the type specified in JSON and YAML prompts.
    /// </summary>
    public const string TypeDiscriminator = "required";

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
        this._functions = functions;
        this.Functions = functions.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName)).ToList();
    }

    /// <summary>
    /// Fully qualified names of subset of the <see cref="Kernel"/>'s plugins' functions information to provide to the model.
    /// </summary>
    [JsonPropertyName("functions")]
    [JsonConverter(typeof(FunctionNameFormatJsonConverter))]
    public IList<string>? Functions { get; set; }

    /// <summary>
    /// The maximum number of function auto-invokes that can be made in a single user request.
    /// </summary>
    /// <remarks>
    /// After this number of iterations as part of a single user request is reached, auto-invocation
    /// will be disabled. This is a safeguard against possible runaway execution if the model routinely re-requests
    /// the same function over and over. To disable auto invocation, this can be set to 0.
    /// </remarks>
    [JsonPropertyName("maximum_auto_invoke_attempts")]
    public int MaximumAutoInvokeAttempts { get; set; } = DefaultMaximumAutoInvokeAttempts;

    /// <summary>
    /// Number of requests that are part of a single user interaction that should include this functions in the request.
    /// </summary>
    /// <remarks>
    /// This should be greater than or equal to <see cref="MaximumAutoInvokeAttempts"/>.
    /// Once this limit is reached, the functions will no longer be included in subsequent requests that are part of the user operation, e.g.
    /// if this is 1, the first request will include the functions, but the subsequent response sending back the functions' result
    /// will not include the functions for further use.
    /// </remarks>
    [JsonPropertyName("maximum_use_attempts")]
    public int MaximumUseAttempts { get; set; } = 1;

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
            throw new KernelException("Auto-invocation for Required choice behavior is not supported when no kernel is provided.");
        }

        List<KernelFunction>? availableFunctions = null;
        bool allowAnyRequestedKernelFunction = false;

        // Handle functions provided via the 'Functions' property as function fully qualified names.
        if (this.Functions is { } functionFQNs && functionFQNs.Any())
        {
            availableFunctions = [];

            foreach (var functionFQN in functionFQNs)
            {
                var nameParts = FunctionName.Parse(functionFQN);

                // Check if the function is available in the kernel. If it is, then connectors can find it for auto-invocation later.
                if (context.Kernel!.Plugins.TryGetFunction(nameParts.PluginName, nameParts.Name, out var function))
                {
                    availableFunctions.Add(function);
                    continue;
                }

                // If auto-invocation is requested and no function is found in the kernel, fail early.
                if (autoInvoke)
                {
                    throw new KernelException($"The specified function {functionFQN} is not available in the kernel.");
                }

                // Check if the function instance was provided via the constructor for manual-invocation.
                function = this._functions?.FirstOrDefault(f => f.Name == nameParts.Name && f.PluginName == nameParts.PluginName);
                if (function is not null)
                {
                    availableFunctions.Add(function);
                    continue;
                }

                throw new KernelException($"No instance of the specified function {functionFQN} is found.");
            }
        }
        // Provide all functions from the kernel.
        else if (context.Kernel is not null)
        {
            allowAnyRequestedKernelFunction = true;

            foreach (var plugin in context.Kernel.Plugins)
            {
                availableFunctions ??= [];
                availableFunctions.AddRange(plugin);
            }
        }

        return new FunctionChoiceBehaviorConfiguration()
        {
            Choice = FunctionChoice.Required,
            Functions = availableFunctions,
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts,
            MaximumUseAttempts = this.MaximumUseAttempts,
            AllowAnyRequestedKernelFunction = allowAnyRequestedKernelFunction
        };
    }
}
