// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Globalization;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Services;

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
    /// Executes functions using the current resources loaded in the context
    /// </summary>
    public Kernel Runner { get; }

    /// <summary>
    /// AI service provider
    /// </summary>
    public IAIServiceProvider ServiceProvider { get; }

    /// <summary>
    /// AIService selector implementation
    /// </summary>
    internal IAIServiceSelector ServiceSelector { get; }

    /// <summary>
    /// Function invoking event handler wrapper
    /// </summary>
    internal EventHandlerWrapper<FunctionInvokingEventArgs>? FunctionInvokingHandler { get; private set; }

    /// <summary>
    /// Function invoked event handler wrapper
    /// </summary>
    internal EventHandlerWrapper<FunctionInvokedEventArgs>? FunctionInvokedHandler { get; private set; }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="kernel">Kernel reference</param>
    /// <param name="serviceProvider">AI service provider</param>
    /// <param name="serviceSelector">AI service selector</param>
    /// <param name="variables">Context variables to include in context.</param>
    /// <param name="invokingWrapper">Event handler wrapper to be used in context</param>
    /// <param name="invokedWrapper">Event handler wrapper to be used in context</param>
    /// <param name="culture">Culture related to the context</param>
    internal SKContext(
        Kernel kernel,
        IAIServiceProvider serviceProvider,
        IAIServiceSelector serviceSelector,
        ContextVariables? variables = null,
        EventHandlerWrapper<FunctionInvokingEventArgs>? invokingWrapper = null,
        EventHandlerWrapper<FunctionInvokedEventArgs>? invokedWrapper = null,
        CultureInfo? culture = null)
    {
        Verify.NotNull(kernel, nameof(kernel));

        this.Runner = kernel;
        this.ServiceProvider = serviceProvider;
        this.ServiceSelector = serviceSelector;
        this.Variables = variables ?? new();
        this._culture = culture ?? CultureInfo.CurrentCulture;
        this.FunctionInvokingHandler = invokingWrapper;
        this.FunctionInvokedHandler = invokedWrapper;
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
    /// Create a clone of the current context, using the same kernel references (memory, plugins, logger)
    /// and a new set variables, so that variables can be modified without affecting the original context.
    /// </summary>
    /// <returns>A new context cloned from the current one</returns>
    public SKContext Clone()
        => this.Clone(null);

    /// <summary>
    /// Create a clone of the current context, using the same kernel references (memory, plugins, logger)
    /// and optionally allows overriding the variables and plugins.
    /// </summary>
    /// <param name="variables">Override the variables with the provided ones</param>
    /// <returns>A new context cloned from the current one</returns>
    public SKContext Clone(ContextVariables? variables)
    {
        return new SKContext(
            this.Runner,
            this.ServiceProvider,
            this.ServiceSelector,
            variables ?? this.Variables.Clone(),
            this.FunctionInvokingHandler,
            this.FunctionInvokedHandler,
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

            display += $", Culture = {this.Culture.EnglishName}";

            return display;
        }
    }
}
