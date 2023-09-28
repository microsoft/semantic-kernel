// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Semantic Kernel context.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class SKContext
{
    /// <summary>
    /// Print the processed input, aka the current data after any processing occurred.
    /// </summary>
    /// <returns>Processed input, aka result</returns>
    public string Result => this.Variables.ToString();

    /// <summary>
    /// When a prompt is processed, aka the current data after any model results processing occurred.
    /// (One prompt can have multiple results).
    /// </summary>
    [Obsolete($"ModelResults are now part of {nameof(FunctionResult.Metadata)} property. Use 'ModelResults' key or available extension methods to get model results.")]
    public IReadOnlyCollection<ModelResult> ModelResults => Array.Empty<ModelResult>();

    /// <summary>
    /// The culture currently associated with this context.
    /// </summary>
    public CultureInfo Culture
    {
        get => this._culture;
        set => this._culture = value ?? CultureInfo.CurrentCulture;
    }

    /// <summary>
    /// User variables
    /// </summary>
    public ContextVariables Variables { get; }

    /// <summary>
    /// Read only functions collection
    /// </summary>
    public IReadOnlyFunctionCollection Functions { get; }

    /// <summary>
    /// App logger
    /// </summary>
    public ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Executes functions using the current resources loaded in the context
    /// </summary>
    public IFunctionExecutor Executor { get; }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="functionExecutor">Kernel reference</param>
    /// <param name="variables">Context variables to include in context.</param>
    /// <param name="functions">Functions to include in context.</param>
    /// <param name="loggerFactory">Logger factory to be used in context</param>
    /// <param name="culture">Culture related to the context</param>
    internal SKContext(
        IFunctionExecutor functionExecutor,
        ContextVariables? variables = null,
        IReadOnlyFunctionCollection? functions = null,
        ILoggerFactory? loggerFactory = null,
        CultureInfo? culture = null)
    {
        Verify.NotNull(functionExecutor, nameof(functionExecutor));

        this.Executor = functionExecutor;
        this.Variables = variables ?? new();
        this.Functions = functions ?? NullReadOnlyFunctionCollection.Instance;
        this.LoggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._culture = culture ?? CultureInfo.CurrentCulture;
    }

    /// <summary>
    /// Print the processed input, aka the current data after any processing occurred.
    /// </summary>
    /// <returns>Processed input, aka result.</returns>
    public override string ToString()
    {
        return this.Result;
    }

    /// <summary>
    /// Create a clone of the current context, using the same kernel references (memory, functions, logger)
    /// and a new set variables, so that variables can be modified without affecting the original context.
    /// </summary>
    /// <returns>A new context cloned from the current one</returns>
    public SKContext Clone()
        => this.Clone(null, null);

    /// <summary>
    /// Create a clone of the current context, using the same kernel references (memory, functions, logger)
    /// and optionally allows overriding the variables and functions.
    /// </summary>
    /// <param name="variables">Override the variables with the provided ones</param>
    /// <param name="functions">Override the functions with the provided ones</param>
    /// <returns>A new context cloned from the current one</returns>
    public SKContext Clone(ContextVariables? variables, IReadOnlyFunctionCollection? functions)
    {
        return new SKContext(
            this.Executor,
            variables ?? this.Variables.Clone(),
            functions ?? this.Functions,
            this.LoggerFactory,
            this.Culture);
    }

    /// <summary>
    /// The culture currently associated with this context.
    /// </summary>
    private CultureInfo _culture;

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay
    {
        get
        {
            string display = this.Variables.DebuggerDisplay;

            if (this.Functions is IReadOnlyFunctionCollection functions)
            {
                var view = functions.GetFunctionViews();
                display += $", Functions = {view.Count}";
            }

            display += $", Culture = {this.Culture.EnglishName}";

            return display;
        }
    }
}
