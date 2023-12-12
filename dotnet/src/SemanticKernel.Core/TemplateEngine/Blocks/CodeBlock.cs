// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

#pragma warning disable CA2254 // error strings are used also internally, not just for logging
#pragma warning disable CA1031 // IsCriticalException is an internal utility and should not be used by extensions

// ReSharper disable TemplateIsNotCompileTimeConstantProblem
internal sealed class CodeBlock : Block, ICodeRendering
{
    internal override BlockTypes Type => BlockTypes.Code;

    /// <summary>
    /// Initializes a new instance of the <see cref="CodeBlock"/> class.
    /// </summary>
    /// <param name="content">Block content</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public CodeBlock(string? content, ILoggerFactory? loggerFactory = null)
        : this(new CodeTokenizer(loggerFactory).Tokenize(content), content?.Trim(), loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CodeBlock"/> class.
    /// </summary>
    /// <param name="tokens">A list of blocks</param>
    /// <param name="content">Block content</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public CodeBlock(List<Block> tokens, string? content, ILoggerFactory? loggerFactory = null)
        : base(content?.Trim(), loggerFactory)
    {
        this._tokens = tokens;
    }

    /// <summary>
    /// Gets the list of blocks.
    /// </summary>
    public List<Block> Blocks => this._tokens;

    /// <inheritdoc/>
    public override bool IsValid(out string errorMsg)
    {
        errorMsg = "";

        foreach (Block token in this._tokens)
        {
            if (!token.IsValid(out errorMsg))
            {
                this.Logger.LogError(errorMsg);
                return false;
            }
        }

        if (this._tokens.Count > 0 && this._tokens[0].Type == BlockTypes.NamedArg)
        {
            errorMsg = "Unexpected named argument found. Expected function name first.";
            this.Logger.LogError(errorMsg);
            return false;
        }

        if (this._tokens.Count > 1 && !this.IsValidFunctionCall(out errorMsg))
        {
            return false;
        }

        this._validated = true;

        return true;
    }

    /// <inheritdoc/>
    public ValueTask<object?> RenderCodeAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        if (!this._validated && !this.IsValid(out var error))
        {
            throw new KernelException(error);
        }

        if (this.Logger.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("Rendering code: `{Content}`", this.Content);
        }

        return this._tokens[0].Type switch
        {
            BlockTypes.Value or BlockTypes.Variable => new ValueTask<object?>(((ITextRendering)this._tokens[0]).Render(arguments)),
            BlockTypes.FunctionId => this.RenderFunctionCallAsync((FunctionIdBlock)this._tokens[0], kernel, arguments),
            _ => throw new KernelException($"Unexpected first token type: {this._tokens[0].Type:G}"),
        };
    }

    #region private ================================================================================

    private bool _validated;
    private readonly List<Block> _tokens;

    private async ValueTask<object?> RenderFunctionCallAsync(FunctionIdBlock fBlock, Kernel kernel, KernelArguments? arguments)
    {
        // If the code syntax is {{functionName $varName}} use $varName instead of $input
        // If the code syntax is {{functionName 'value'}} use "value" instead of $input
        if (this._tokens.Count > 1)
        {
            //Cloning the original arguments to avoid side effects - arguments added to the original arguments collection as a result of rendering template variables.
            arguments = this.EnrichFunctionArguments(kernel, fBlock, arguments is null ? new KernelArguments() : new KernelArguments(arguments));
        }
        try
        {
            var result = await kernel.InvokeAsync(fBlock.PluginName, fBlock.FunctionName, arguments).ConfigureAwait(false);

            return result.Value;
        }
        catch (Exception ex)
        {
            this.Logger.LogError(ex, "Function {Plugin}.{Function} execution failed with error {Error}", fBlock.PluginName, fBlock.FunctionName, ex.Message);
            throw;
        }
    }

    private bool IsValidFunctionCall(out string errorMsg)
    {
        errorMsg = "";
        if (this._tokens[0].Type != BlockTypes.FunctionId)
        {
            errorMsg = $"Unexpected second token found: {this._tokens[1].Content}";
            this.Logger.LogError(errorMsg);
            return false;
        }

        if (this._tokens[1].Type is not BlockTypes.Value and not BlockTypes.Variable and not BlockTypes.NamedArg)
        {
            errorMsg = "The first arg of a function must be a quoted string, variable or named argument";
            this.Logger.LogError(errorMsg);
            return false;
        }

        for (int i = 2; i < this._tokens.Count; i++)
        {
            if (this._tokens[i].Type is not BlockTypes.NamedArg)
            {
                errorMsg = $"Functions only support named arguments after the first argument. Argument {i} is not named.";
                this.Logger.LogError(errorMsg);
                return false;
            }
        }

        return true;
    }

    /// <summary>
    /// Adds function arguments. If the first argument is not a named argument, it is added to the arguments collection as the 'input' argument.
    /// Additionally, for the prompt expression - {{MyPlugin.MyFunction p1=$v1}}, the value of the v1 variable will be resolved from the original arguments collection.
    /// Then, the new argument, p1, will be added to the arguments.
    /// </summary>
    /// <param name="kernel">Kernel instance.</param>
    /// <param name="fBlock">Function block.</param>
    /// <param name="arguments">The prompt rendering arguments.</param>
    /// <returns>The function arguments.</returns>
    /// <exception cref="KernelException">Occurs when any argument other than the first is not a named argument.</exception>
    private KernelArguments EnrichFunctionArguments(Kernel kernel, FunctionIdBlock fBlock, KernelArguments arguments)
    {
        var firstArg = this._tokens[1];

        // Sensitive data, logging as trace, disabled by default
        if (this.Logger.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("Passing variable/value: `{Content}`", firstArg.Content);
        }

        // Get the function metadata
        var functionMetadata = kernel.Plugins.GetFunction(fBlock.PluginName, fBlock.FunctionName).Metadata;

        // Check if the function has parameters to be set
        if (functionMetadata.Parameters.Count == 0)
        {
            throw new ArgumentException($"Function {fBlock.PluginName}.{fBlock.FunctionName} does not take any arguments but it is being called in the template with {this._tokens.Count - 1} arguments.");
        }

        string? firstPositionalParameterName = null;
        object? firstPositionalInputValue = null;
        var namedArgsStartIndex = 1;

        if (firstArg.Type is not BlockTypes.NamedArg)
        {
            // Gets the function first parameter name
            firstPositionalParameterName = functionMetadata.Parameters[0].Name;

            firstPositionalInputValue = ((ITextRendering)this._tokens[1]).Render(arguments);
            // Type check is avoided and marshalling is done by the function itself

            // Keep previous trust information when updating the input
            arguments[firstPositionalParameterName] = firstPositionalInputValue;
            namedArgsStartIndex++;
        }

        for (int i = namedArgsStartIndex; i < this._tokens.Count; i++)
        {
            // When casting fails because the block isn't a NamedArg, arg is null
            if (this._tokens[i] is not NamedArgBlock arg)
            {
                var errorMsg = "Functions support up to one positional argument";
                this.Logger.LogError(errorMsg);
                throw new KernelException($"Unexpected first token type: {this._tokens[i].Type:G}");
            }

            // Sensitive data, logging as trace, disabled by default
            if (this.Logger.IsEnabled(LogLevel.Trace))
            {
                this.Logger.LogTrace("Passing variable/value: `{Content}`", arg.Content);
            }

            // Check if the positional parameter clashes with a named parameter
            if (firstPositionalParameterName is not null && string.Equals(firstPositionalParameterName, arg.Name, StringComparison.OrdinalIgnoreCase))
            {
                throw new ArgumentException($"Ambiguity found as a named parameter '{arg.Name}' cannot be set for the first parameter when there is also a positional value: '{firstPositionalInputValue}' provided. Function: {fBlock.PluginName}.{fBlock.FunctionName}");
            }

            arguments[arg.Name] = arg.GetValue(arguments);
        }

        return arguments;
    }
    #endregion
}
// ReSharper restore TemplateIsNotCompileTimeConstantProblem
#pragma warning restore CA2254
