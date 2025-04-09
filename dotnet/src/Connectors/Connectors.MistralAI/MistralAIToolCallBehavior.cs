// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>Represents a behavior for Mistral tool calls.</summary>
public abstract class MistralAIToolCallBehavior
{
    // NOTE: Right now, the only tools that are available are for function calling. In the future,
    // this class can be extended to support additional kinds of tools, including composite ones:
    // the MistralAIPromptExecutionSettings has a single ToolCallBehavior property, but we could
    // expose a `public static ToolCallBehavior Composite(params ToolCallBehavior[] behaviors)`
    // or the like to allow multiple distinct tools to be provided, should that be appropriate.
    // We can also consider additional forms of tools, such as ones that dynamically examine
    // the Kernel, KernelArguments, etc.

    /// <summary>
    /// The default maximum number of tool-call auto-invokes that can be made in a single request.
    /// </summary>
    /// <remarks>
    /// After this number of iterations as part of a single user request is reached, auto-invocation
    /// will be disabled (e.g. <see cref="AutoInvokeKernelFunctions"/> will behave like <see cref="EnableKernelFunctions"/>)).
    /// This is a safeguard against possible runaway execution if the model routinely re-requests
    /// the same function over and over. It is currently hardcoded, but in the future it could
    /// be made configurable by the developer. Other configuration is also possible in the future,
    /// such as a delegate on the instance that can be invoked upon function call failure (e.g. failure
    /// to find the requested function, failure to invoke the function, etc.), with behaviors for
    /// what to do in such a case, e.g. respond to the model telling it to try again. With parallel tool call
    /// support, where the model can request multiple tools in a single response, it is significantly
    /// less likely that this limit is reached, as most of the time only a single request is needed.
    /// </remarks>
    private const int DefaultMaximumAutoInvokeAttempts = 5;

    /// <summary>
    /// Gets an instance that will provide all of the <see cref="Kernel"/>'s plugins' function information.
    /// Function call requests from the model will be propagated back to the caller.
    /// </summary>
    /// <remarks>
    /// If no <see cref="Kernel"/> is available, no function information will be provided to the model.
    /// </remarks>
    public static MistralAIToolCallBehavior EnableKernelFunctions { get; } = new KernelFunctions(autoInvoke: false);

    /// <summary>
    /// Gets an instance that will both provide all of the <see cref="Kernel"/>'s plugins' function information
    /// to the model and attempt to automatically handle any function call requests.
    /// </summary>
    /// <remarks>
    /// When successful, tool call requests from the model become an implementation detail, with the service
    /// handling invoking any requested functions and supplying the results back to the model.
    /// If no <see cref="Kernel"/> is available, no function information will be provided to the model.
    /// </remarks>
    public static MistralAIToolCallBehavior AutoInvokeKernelFunctions { get; } = new KernelFunctions(autoInvoke: true);

    /// <summary>Gets an instance that will provide the specified list of functions to the model.</summary>
    /// <param name="functions">The functions that should be made available to the model.</param>
    /// <param name="autoInvoke">true to attempt to automatically handle function call requests; otherwise, false.</param>
    /// <returns>
    /// The <see cref="MistralAIToolCallBehavior"/> that may be set into <see cref="MistralAIPromptExecutionSettings.ToolCallBehavior"/>
    /// to indicate that the specified functions should be made available to the model.
    /// The model is forced to call a function from the list of functions provided.
    /// </returns>
    public static MistralAIToolCallBehavior RequiredFunctions(IEnumerable<KernelFunction> functions, bool autoInvoke = false)
    {
        Verify.NotNull(functions);
        return new AnyFunction(functions, autoInvoke);
    }

    /// <summary>
    /// Gets an instance that will both provide all of the <see cref="Kernel"/>'s plugins' function information
    /// to the model but not any function call requests.
    /// </summary>
    /// <remarks>
    /// When successful, tool call requests from the model become an implementation detail, with the service
    /// handling invoking any requested functions and supplying the results back to the model.
    /// If no <see cref="Kernel"/> is available, no function information will be provided to the model.
    /// </remarks>
    public static MistralAIToolCallBehavior NoKernelFunctions { get; } = new NoneKernelFunctions();

    /// <summary>Initializes the instance; prevents external instantiation.</summary>
    private MistralAIToolCallBehavior(bool autoInvoke)
    {
        this.MaximumAutoInvokeAttempts = autoInvoke ? DefaultMaximumAutoInvokeAttempts : 0;
    }

    /// <summary>
    /// Options to control tool call result serialization behavior.
    /// </summary>
    public virtual JsonSerializerOptions? ToolCallResultSerializerOptions { get; set; }

    /// <summary>Gets how many requests are part of a single interaction should include this tool in the request.</summary>
    /// <remarks>
    /// This should be greater than or equal to <see cref="MaximumAutoInvokeAttempts"/>. It defaults to <see cref="int.MaxValue"/>.
    /// Once this limit is reached, the tools will no longer be included in subsequent retries as part of the operation, e.g.
    /// if this is 1, the first request will include the tools, but the subsequent response sending back the tool's result
    /// will not include the tools for further use.
    /// </remarks>
    internal virtual int MaximumUseAttempts => int.MaxValue;

    /// <summary>Gets how many tool call request/response roundtrips are supported with auto-invocation.</summary>
    /// <remarks>
    /// To disable auto invocation, this can be set to 0.
    /// </remarks>
    internal int MaximumAutoInvokeAttempts { get; }

    /// <summary>
    /// Gets whether validation against a specified list is required before allowing the model to request a function from the kernel.
    /// </summary>
    /// <value>true if it's ok to invoke any kernel function requested by the model if it's found; false if a request needs to be validated against an allow list.</value>
    internal virtual bool AllowAnyRequestedKernelFunction => false;

    /// <summary>Configures the <paramref name="request"/> with any tools this <see cref="MistralAIToolCallBehavior"/> provides.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> used for the operation. This can be queried to determine what tools to provide into the <paramref name="request"/>.</param>
    /// <param name="request">The destination <see cref="ChatCompletionRequest"/> to configure.</param>
    internal abstract void ConfigureRequest(Kernel? kernel, ChatCompletionRequest request);

    /// <summary>
    /// Represents a <see cref="MistralAIToolCallBehavior"/> that will provide to the model all available functions from a
    /// <see cref="Kernel"/> provided by the client.
    /// </summary>
    internal sealed class KernelFunctions : MistralAIToolCallBehavior
    {
        internal KernelFunctions(bool autoInvoke) : base(autoInvoke) { }

        public override string ToString() => $"{nameof(KernelFunctions)}(autoInvoke:{this.MaximumAutoInvokeAttempts != 0})";

        internal IEnumerable<KernelFunctionMetadata>? GetFunctionsMetadata(Kernel? kernel)
        {
            // Provide all functions from the kernel.
            return kernel?.Plugins?.GetFunctionsMetadata();
        }

        internal override void ConfigureRequest(Kernel? kernel, ChatCompletionRequest request)
        {
            var functionsMetadata = kernel?.Plugins?.GetFunctionsMetadata();
            if (functionsMetadata is null)
            {
                return;
            }

            // If auto-invocation is specified, we need a kernel to be able to invoke the functions.
            // Lack of a kernel is fatal: we don't want to tell the model we can handle the functions
            // and then fail to do so, so we fail before we get to that point. This is an error
            // on the consumers behalf: if they specify auto-invocation with any functions, they must
            // specify the kernel and the kernel must contain those functions.
            bool autoInvoke = this.MaximumAutoInvokeAttempts > 0;
            if (autoInvoke && kernel is null)
            {
                throw new KernelException($"Auto-invocation with {nameof(KernelFunctions)} is not supported when no kernel is provided.");
            }

            request.ToolChoice = "auto";

            foreach (var functionMetadata in functionsMetadata)
            {
                request.AddTool(ToMistralTool(functionMetadata));
            }
        }

        internal override bool AllowAnyRequestedKernelFunction => true;
    }

    /// <summary>
    /// Represents a <see cref="MistralAIToolCallBehavior"/> that provides a specified list of functions to the model.
    /// </summary>
    internal sealed class AnyFunction(IEnumerable<KernelFunction> functions, bool autoInvoke) : MistralAIToolCallBehavior(autoInvoke)
    {
        private readonly IEnumerable<KernelFunctionMetadata>? _kernelFunctionMetadata = functions.Select(f => f.Metadata);

        public override string ToString() => $"{nameof(AnyFunction)}(autoInvoke:{this.MaximumAutoInvokeAttempts != 0}): {string.Join(", ", this._kernelFunctionMetadata!.Select(f => f.Name))}";

        internal override void ConfigureRequest(Kernel? kernel, ChatCompletionRequest request)
        {
            if (this._kernelFunctionMetadata is null)
            {
                return;
            }

            // If auto-invocation is specified, we need a kernel to be able to invoke the functions.
            // Lack of a kernel is fatal: we don't want to tell the model we can handle the functions
            // and then fail to do so, so we fail before we get to that point. This is an error
            // on the consumers behalf: if they specify auto-invocation with any functions, they must
            // specify the kernel and the kernel must contain those functions.
            bool autoInvoke = base.MaximumAutoInvokeAttempts > 0;
            if (autoInvoke && kernel is null)
            {
                throw new KernelException($"Auto-invocation with {nameof(AnyFunction)} is not supported when no kernel is provided.");
            }

            foreach (var metadata in this._kernelFunctionMetadata)
            {
                // Make sure that if auto-invocation is specified, every enabled function can be found in the kernel.
                if (autoInvoke)
                {
                    Debug.Assert(kernel is not null);
                    if (!kernel!.Plugins.TryGetFunction(metadata.PluginName, metadata.Name, out _))
                    {
                        throw new KernelException($"The specified {nameof(RequiredFunctions)} function {metadata.PluginName}-{metadata.Name} is not available in the kernel.");
                    }
                }
            }

            request.ToolChoice = "any";

            foreach (var functionMetadata in this._kernelFunctionMetadata)
            {
                request.AddTool(ToMistralTool(functionMetadata));
            }
        }

        /// <summary>Gets how many requests are part of a single interaction should include this tool in the request.</summary>
        /// <remarks>
        /// Unlike <see cref="KernelFunctions"/>, this must use 1 as the maximum
        /// use attempts. Otherwise, every call back to the model _requires_ it to invoke the function (as opposed
        /// to allows it), which means we end up doing the same work over and over and over until the maximum is reached.
        /// Thus for "requires", we must send the tool information only once.
        /// </remarks>
        internal override int MaximumUseAttempts => 1;
    }

    /// <summary>
    /// Represents a <see cref="MistralAIToolCallBehavior"/> that will provide to the model all available functions from a
    /// <see cref="Kernel"/> provided by the client and specifies the cool choice "none".
    /// When tool choice is set to none the model won't call a function and will generate a message instead.
    /// </summary>
    internal sealed class NoneKernelFunctions : MistralAIToolCallBehavior
    {
        internal NoneKernelFunctions() : base(false) { }

        public override string ToString() => "{nameof(NoneKernelFunctions)}";

        internal IEnumerable<KernelFunctionMetadata>? GetFunctionsMetadata(Kernel? kernel)
        {
            // Provide all functions from the kernel.
            return kernel?.Plugins?.GetFunctionsMetadata();
        }

        internal override void ConfigureRequest(Kernel? kernel, ChatCompletionRequest request)
        {
            var functionsMetadata = kernel?.Plugins?.GetFunctionsMetadata();
            if (functionsMetadata is null)
            {
                return;
            }

            request.ToolChoice = "none";

            foreach (var functionMetadata in functionsMetadata)
            {
                request.AddTool(ToMistralTool(functionMetadata));
            }
        }

        internal override bool AllowAnyRequestedKernelFunction => true;
    }

    private static MistralTool ToMistralTool(KernelFunctionMetadata metadata)
    {
        return new MistralTool("function", new MistralFunction(metadata));
    }
}
