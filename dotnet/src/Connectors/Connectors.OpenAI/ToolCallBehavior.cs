// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>Represents a behavior for OpenAI tool calls.</summary>
public abstract class ToolCallBehavior
{
    // NOTE: Right now, the only tools that are available are for function calling. In the future,
    // this class can be extended to support additional kinds of tools, including composite ones:
    // the OpenAIPromptExecutionSettings has a single ToolCallBehavior property, but we could
    // expose a `public static ToolCallBehavior Composite(params ToolCallBehavior[] behaviors)`
    // or the like to allow multiple distinct tools to be provided, should that be appropriate.
    // We can also consider additional forms of tools, such as ones that dynamically examine
    // the Kernel, KernelArguments, etc., and dynamically contribute tools to the ChatCompletionsOptions.

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
    public static ToolCallBehavior EnableKernelFunctions { get; } = new KernelFunctions(autoInvoke: false);

    /// <summary>
    /// Gets an instance that will both provide all of the <see cref="Kernel"/>'s plugins' function information
    /// to the model and attempt to automatically handle any function call requests.
    /// </summary>
    /// <remarks>
    /// When successful, tool call requests from the model become an implementation detail, with the service
    /// handling invoking any requested functions and supplying the results back to the model.
    /// If no <see cref="Kernel"/> is available, no function information will be provided to the model.
    /// </remarks>
    public static ToolCallBehavior AutoInvokeKernelFunctions { get; } = new KernelFunctions(autoInvoke: true);

    /// <summary>Gets an instance that will provide the specified list of functions to the model.</summary>
    /// <param name="functions">The functions that should be made available to the model.</param>
    /// <param name="autoInvoke">true to attempt to automatically handle function call requests; otherwise, false.</param>
    /// <returns>
    /// The <see cref="ToolCallBehavior"/> that may be set into <see cref="OpenAIPromptExecutionSettings.ToolCallBehavior"/>
    /// to indicate that the specified functions should be made available to the model.
    /// </returns>
    public static ToolCallBehavior EnableFunctions(IEnumerable<OpenAIFunction> functions, bool autoInvoke = false)
    {
        Verify.NotNull(functions);
        return new EnabledFunctions(functions, autoInvoke);
    }

    /// <summary>Gets an instance that will request the model to use the specified function.</summary>
    /// <param name="function">The function the model should request to use.</param>
    /// <param name="autoInvoke">true to attempt to automatically handle function call requests; otherwise, false.</param>
    /// <returns>
    /// The <see cref="ToolCallBehavior"/> that may be set into <see cref="OpenAIPromptExecutionSettings.ToolCallBehavior"/>
    /// to indicate that the specified function should be requested by the model.
    /// </returns>
    [Experimental("SKEXP0013")]
    public static ToolCallBehavior RequireFunction(OpenAIFunction function, bool autoInvoke = false)
    {
        Verify.NotNull(function);
        return new RequiredFunction(function, autoInvoke);
    }

    /// <summary>Initializes the instance; prevents external instantiation.</summary>
    private ToolCallBehavior(bool autoInvoke)
    {
        this.MaximumAutoInvokeAttempts = autoInvoke ? DefaultMaximumAutoInvokeAttempts : 0;
    }

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

    /// <summary>Configures the <paramref name="options"/> with any tools this <see cref="ToolCallBehavior"/> provides.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> used for the operation. This can be queried to determine what tools to provide into the <paramref name="options"/>.</param>
    /// <param name="options">The destination <see cref="ChatCompletionsOptions"/> to configure.</param>
    internal abstract void ConfigureOptions(Kernel? kernel, ChatCompletionsOptions options);

    /// <summary>
    /// Represents a <see cref="ToolCallBehavior"/> that will provide to the model all available functions from a
    /// <see cref="Kernel"/> provided by the client.
    /// </summary>
    internal sealed class KernelFunctions : ToolCallBehavior
    {
        internal KernelFunctions(bool autoInvoke) : base(autoInvoke) { }

        public override string ToString() => $"{nameof(KernelFunctions)}(autoInvoke:{this.MaximumAutoInvokeAttempts != 0})";

        internal override void ConfigureOptions(Kernel? kernel, ChatCompletionsOptions options)
        {
            // If no kernel is provided, we don't have any tools to provide.
            if (kernel is not null)
            {
                // Provide all functions from the kernel.
                IList<KernelFunctionMetadata> functions = kernel.Plugins.GetFunctionsMetadata();
                if (functions.Count > 0)
                {
                    options.ToolChoice = ChatCompletionsToolChoice.Auto;
                    for (int i = 0; i < functions.Count; i++)
                    {
                        options.Tools.Add(new ChatCompletionsFunctionToolDefinition(functions[i].ToOpenAIFunction().ToFunctionDefinition()));
                    }
                }
            }
        }

        internal override bool AllowAnyRequestedKernelFunction => true;
    }

    /// <summary>
    /// Represents a <see cref="ToolCallBehavior"/> that provides a specified list of functions to the model.
    /// </summary>
    internal sealed class EnabledFunctions : ToolCallBehavior
    {
        private readonly OpenAIFunction[] _openAIFunctions;
        private readonly ChatCompletionsFunctionToolDefinition[] _functions;

        public EnabledFunctions(IEnumerable<OpenAIFunction> functions, bool autoInvoke) : base(autoInvoke)
        {
            this._openAIFunctions = functions.ToArray();

            var defs = new ChatCompletionsFunctionToolDefinition[this._openAIFunctions.Length];
            for (int i = 0; i < defs.Length; i++)
            {
                defs[i] = new ChatCompletionsFunctionToolDefinition(this._openAIFunctions[i].ToFunctionDefinition());
            }
            this._functions = defs;
        }

        public override string ToString() => $"{nameof(EnabledFunctions)}(autoInvoke:{this.MaximumAutoInvokeAttempts != 0}): {string.Join(", ", this._functions.Select(f => f.Name))}";

        internal override void ConfigureOptions(Kernel? kernel, ChatCompletionsOptions options)
        {
            OpenAIFunction[] openAIFunctions = this._openAIFunctions;
            ChatCompletionsFunctionToolDefinition[] functions = this._functions;
            Debug.Assert(openAIFunctions.Length == functions.Length);

            if (openAIFunctions.Length > 0)
            {
                bool autoInvoke = base.MaximumAutoInvokeAttempts > 0;

                // If auto-invocation is specified, we need a kernel to be able to invoke the functions.
                // Lack of a kernel is fatal: we don't want to tell the model we can handle the functions
                // and then fail to do so, so we fail before we get to that point. This is an error
                // on the consumers behalf: if they specify auto-invocation with any functions, they must
                // specify the kernel and the kernel must contain those functions.
                if (autoInvoke && kernel is null)
                {
                    throw new KernelException($"Auto-invocation with {nameof(EnabledFunctions)} is not supported when no kernel is provided.");
                }

                options.ToolChoice = ChatCompletionsToolChoice.Auto;
                for (int i = 0; i < openAIFunctions.Length; i++)
                {
                    // Make sure that if auto-invocation is specified, every enabled function can be found in the kernel.
                    if (autoInvoke)
                    {
                        Debug.Assert(kernel is not null);
                        OpenAIFunction f = openAIFunctions[i];
                        if (!kernel!.Plugins.TryGetFunction(f.PluginName, f.FunctionName, out _))
                        {
                            throw new KernelException($"The specified {nameof(EnabledFunctions)} function {f.FullyQualifiedName} is not available in the kernel.");
                        }
                    }

                    // Add the function.
                    options.Tools.Add(functions[i]);
                }
            }
        }
    }

    /// <summary>Represents a <see cref="ToolCallBehavior"/> that requests the model use a specific function.</summary>
    internal sealed class RequiredFunction : ToolCallBehavior
    {
        private readonly ChatCompletionsFunctionToolDefinition _tool;
        private readonly ChatCompletionsToolChoice _choice;

        public RequiredFunction(OpenAIFunction function, bool autoInvoke) : base(autoInvoke)
        {
            this._tool = new ChatCompletionsFunctionToolDefinition(function.ToFunctionDefinition());
            this._choice = new ChatCompletionsToolChoice(this._tool);
        }

        public override string ToString() => $"{nameof(RequiredFunction)}(autoInvoke:{this.MaximumAutoInvokeAttempts != 0}): {this._tool.Name}";

        internal override void ConfigureOptions(Kernel? kernel, ChatCompletionsOptions options)
        {
            options.ToolChoice = this._choice;
            options.Tools.Add(this._tool);
        }

        /// <summary>Gets how many requests are part of a single interaction should include this tool in the request.</summary>
        /// <remarks>
        /// Unlike <see cref="EnabledFunctions"/> and <see cref="KernelFunctions"/>, this must use 1 as the maximum
        /// use attempts. Otherwise, every call back to the model _requires_ it to invoke the function (as opposed
        /// to allows it), which means we end up doing the same work over and over and over until the maximum is reached.
        /// Thus for "requires", we must send the tool information only once.
        /// </remarks>
        internal override int MaximumUseAttempts => 1;
    }
}
