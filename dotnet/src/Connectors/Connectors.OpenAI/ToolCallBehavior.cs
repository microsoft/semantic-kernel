// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
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
            if (kernel is not null)
            {
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
    }

    /// <summary>
    /// Represents a <see cref="ToolCallBehavior"/> that provides a specified list of functions to the model.
    /// </summary>
    internal sealed class EnabledFunctions : ToolCallBehavior
    {
        private readonly List<ChatCompletionsFunctionToolDefinition> _functions;

        public EnabledFunctions(IEnumerable<OpenAIFunction> functions, bool autoInvoke) : base(autoInvoke)
        {
            this._functions = functions.Select(f => new ChatCompletionsFunctionToolDefinition(f.ToFunctionDefinition())).ToList();
        }

        public override string ToString() => $"{nameof(EnabledFunctions)}(autoInvoke:{this.MaximumAutoInvokeAttempts != 0}): {string.Join(", ", this._functions.Select(f => f.Name))}";

        internal override void ConfigureOptions(Kernel? kernel, ChatCompletionsOptions options)
        {
            if (this._functions.Count > 0)
            {
                options.ToolChoice = ChatCompletionsToolChoice.Auto;
                foreach (var f in this._functions)
                {
                    options.Tools.Add(f);
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
