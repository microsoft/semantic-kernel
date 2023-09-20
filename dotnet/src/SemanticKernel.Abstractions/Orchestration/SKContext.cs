// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions;

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
    public IReadOnlyCollection<ModelResult> ModelResults { get; set; } = Array.Empty<ModelResult>();

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
    /// Read only skills collection
    /// </summary>
    public IReadOnlySkillCollection Skills { get; }

    /// <summary>
    /// App logger
    /// </summary>
    public ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Kernel context reference
    /// </summary>
    public IKernel Kernel => this.GetKernelContext();

    /// <summary>
    /// Spawns the kernel for the context.
    /// </summary>
    /// <remarks>
    /// The kernel context is a lightweight instance of the main kernel with its services.
    /// </remarks>
    /// <returns>Kernel reference</returns>
    private IKernel GetKernelContext()
        => this._originalKernel; // TODO: Clone a lightweight kernel instead of returning the same instance

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="kernel">Kernel reference</param>
    /// <param name="variables">Context variables to include in context.</param>
    /// <param name="skills">Skills to include in context.</param>
    public SKContext(
        IKernel kernel,
        ContextVariables? variables = null,
        IReadOnlySkillCollection? skills = null)
    {
        Verify.NotNull(kernel, nameof(kernel));

        this._originalKernel = kernel;
        this.Variables = variables ?? new();
        this.Skills = skills ?? NullReadOnlySkillCollection.Instance;
        this.LoggerFactory = kernel.LoggerFactory;
        this._culture = CultureInfo.CurrentCulture;
    }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="kernel">Kernel instance parameter</param>
    /// <param name="variables">Context variables to include in context.</param>
    public SKContext(
        IKernel kernel,
        ContextVariables? variables = null) : this(kernel, variables, kernel.Skills)
    {
    }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="kernel">Kernel instance parameter</param>
    /// <param name="skills">Skills to include in context.</param>
    public SKContext(
        IKernel kernel,
        IReadOnlySkillCollection? skills = null) : this(kernel, null, skills)
    {
    }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="kernel">Kernel instance parameter</param>
    public SKContext(IKernel kernel) : this(kernel, null, kernel.Skills)
    {
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
    /// Create a clone of the current context, using the same kernel references (memory, skills, logger)
    /// and a new set variables, so that variables can be modified without affecting the original context.
    /// </summary>
    /// <returns>A new context copied from the current one</returns>
    public SKContext Clone()
    {
        return new SKContext(
            kernel: this._originalKernel,
            variables: this.Variables.Clone())
        {
            Culture = this.Culture,
        };
    }

    /// <summary>
    /// The culture currently associated with this context.
    /// </summary>
    private CultureInfo _culture;

    /// <summary>
    /// Kernel instance reference for this context.
    /// </summary>
    private readonly IKernel _originalKernel;

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay
    {
        get
        {
            string display = this.Variables.DebuggerDisplay;

            if (this.Skills is IReadOnlySkillCollection skills)
            {
                var view = skills.GetFunctionViews();
                display += $", Skills = {view.Count}";
            }

            display += $", Culture = {this.Culture.EnglishName}";

            return display;
        }
    }
}
