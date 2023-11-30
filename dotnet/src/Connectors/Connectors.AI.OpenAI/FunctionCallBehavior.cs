// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>Represents a behavior for OpenAI function calling.</summary>
public abstract class FunctionCallBehavior
{
    /// <summary>
    /// Gets an instance that will both provide all of the <see cref="Kernel"/>'s plugins' function information
    /// Function call requests will be propagated back to the caller.
    /// </summary>
    /// <remarks>
    /// If no <see cref="Kernel"/> is available, no function information will be provided to the service.
    /// </remarks>
    public static FunctionCallBehavior EnableKernelFunctions { get; } = new KernelFunctions(autoInvoke: false);

    /// <summary>
    /// Gets an instance that will both provide all of the <see cref="Kernel"/>'s plugins' function information
    /// to the service and attempt to automatically handle any function call requests.
    /// </summary>
    /// <remarks>
    /// If no <see cref="Kernel"/> is available, no function information will be provided to the service.
    /// </remarks>
    public static FunctionCallBehavior AutoInvokeKernelFunctions { get; } = new KernelFunctions(autoInvoke: true);

    /// <summary>Gets an instance that will provide the specified list of functions to the service.</summary>
    /// <param name="functions">The functions that should be made available to the service.</param>
    /// <param name="autoInvoke">true to attempt to automatically handle a function call request; otherwise, false.</param>
    /// <returns></returns>
    public static FunctionCallBehavior EnableFunctions(IEnumerable<OpenAIFunction> functions, bool autoInvoke = false)
    {
        Verify.NotNull(functions);
        return new EnabledFunctions(functions, autoInvoke);
    }

    /// <summary>Gets an instance that will request the service to use the specified function.</summary>
    /// <param name="function">The function the service should request to use.</param>
    /// <param name="autoInvoke">true to attempt to automatically handle a function call request; otherwise, false.</param>
    /// <returns></returns>
    public static FunctionCallBehavior RequireFunction(OpenAIFunction function, bool autoInvoke = false)
    {
        Verify.NotNull(function);
        return new RequiredFunction(function, autoInvoke);
    }

    /// <summary>Initializes the instance.</summary>
    /// <param name="autoInvoke">true to attempt to automatically handle a function call request; otherwise, false.</param>
    private FunctionCallBehavior(bool autoInvoke) => this.AutoInvoke = autoInvoke;

    /// <summary>Gets whether to attempt to auto-invoke functions based on function call requests.</summary>
    internal bool AutoInvoke { get; }

    /// <summary>
    /// Represents a <see cref="FunctionCallBehavior"/> that will provide to the service all available functions from a
    /// <see cref="Kernel"/> provided to the client.
    /// </summary>
    internal sealed class KernelFunctions : FunctionCallBehavior
    {
        internal KernelFunctions(bool autoInvoke) : base(autoInvoke) { }

        public override string ToString() => $"KernelFunctions(autoInvoke:{this.AutoInvoke})";
    }

    /// <summary>
    /// Represents a <see cref="FunctionCallBehavior"/> that provides a specified list of functions to the service.
    /// </summary>
    internal sealed class EnabledFunctions : FunctionCallBehavior
    {
        public EnabledFunctions(IEnumerable<OpenAIFunction> functions, bool autoInvoke) : base(autoInvoke) =>
            this.Functions = functions.Select(f => f.ToFunctionDefinition()).ToList();

        /// <summary>Gets the available list of functions.</summary>
        public List<FunctionDefinition> Functions { get; }

        public override string ToString() => $"EnabledFunctions(autoInvoke:{this.AutoInvoke}): {string.Join(", ", this.Functions.Select(f => f.Name))}";
    }

    /// <summary>Represents a <see cref="FunctionCallBehavior"/> that requests the service use a specific function.</summary>
    internal sealed class RequiredFunction : FunctionCallBehavior
    {
        private FunctionDefinition[]? _functionArray;

        public RequiredFunction(OpenAIFunction function, bool autoInvoke) : base(autoInvoke) =>
            this.Function = function.ToFunctionDefinition();

        /// <summary>Gets the target function.</summary>
        public FunctionDefinition Function { get; }

        /// <summary>Gets the target function wrapped in an array.</summary>
        public FunctionDefinition[] FunctionArray => this._functionArray ??= new[] { this.Function };

        public override string ToString() => $"RequiredFunction(autoInvoke:{this.AutoInvoke}): {this.Function.Name}";
    }
}
