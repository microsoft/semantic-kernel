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
    /// List of the fully qualified names of the functions that the model can choose from.
    /// </summary>
    private readonly IEnumerable<string>? _functionFQNs;

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
    }

    /// <summary>
    /// Fully qualified names of subset of the <see cref="Kernel"/>'s plugins' functions information to provide to the model.
    /// </summary>
    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions
    {
        get => this._functionFQNs;
        init
        {
            if (value?.Count() > 0 && this._functions?.Count() > 0)
            {
                throw new KernelException("Functions are already provided via the constructor.");
            }

            this._functionFQNs = value;
        }
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

        List<KernelFunction>? requiredFunctions = null;
        bool allowAnyRequestedKernelFunction = false;

        // Handle functions provided via constructor as function instances.
        if (this._functions is { } functions && functions.Any())
        {
            // Make sure that every function can be found in the kernel.
            if (autoInvoke)
            {
                foreach (var function in functions)
                {
                    if (!context.Kernel!.Plugins.TryGetFunction(function.PluginName, function.Name, out _))
                    {
                        throw new KernelException($"The specified function {function.PluginName}.{function.Name} is not available in the kernel.");
                    }
                }
            }

            requiredFunctions = functions.ToList();
        }
        // Handle functions provided via the 'Functions' property as function fully qualified names.
        else if (this.Functions is { } functionFQNs && functionFQNs.Any())
        {
            requiredFunctions = [];

            foreach (var functionFQN in functionFQNs)
            {
                // Make sure that every function can be found in the kernel.
                var name = FunctionName.Parse(functionFQN, FunctionNameSeparator);

                if (!context.Kernel!.Plugins.TryGetFunction(name.PluginName, name.Name, out var function))
                {
                    throw new KernelException($"The specified function {functionFQN} is not available in the kernel.");
                }

                requiredFunctions.Add(function);
            }
        }
        // Provide all functions from the kernel.
        else if (context.Kernel is not null)
        {
            allowAnyRequestedKernelFunction = true;

            foreach (var plugin in context.Kernel.Plugins)
            {
                requiredFunctions ??= [];
                requiredFunctions.AddRange(plugin);
            }
        }

        return new FunctionChoiceBehaviorConfiguration()
        {
            RequiredFunctions = requiredFunctions,
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts,
            MaximumUseAttempts = this.MaximumUseAttempts,
            AllowAnyRequestedKernelFunction = allowAnyRequestedKernelFunction
        };
    }
}
