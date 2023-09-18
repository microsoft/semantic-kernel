// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Globalization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Semantic Kernel context.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class SKContext
{
    /// <summary>
    /// The culture currently associated with this context.
    /// </summary>
    private CultureInfo _culture;

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
    /// Read only skills collection
    /// </summary>
    public IReadOnlySkillCollection Skills { get; }

    /// <summary>
    /// App logger
    /// </summary>
    public ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="variables">Context variables to include in context.</param>
    /// <param name="skills">Skills to include in context.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public SKContext(
        ContextVariables? variables = null,
        IReadOnlySkillCollection? skills = null,
        ILoggerFactory? loggerFactory = null)
    {
        this.Variables = variables ?? new();
        this.Skills = skills ?? NullReadOnlySkillCollection.Instance;
        this.LoggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._culture = CultureInfo.CurrentCulture;
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
            variables: this.Variables.Clone(),
            skills: this.Skills,
            loggerFactory: this.LoggerFactory)
        {
            Culture = this.Culture,
        };
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay
    {
        get
        {
            string display = this.Variables.DebuggerDisplay;

            if (this.Skills is IReadOnlySkillCollection skills)
            {
                var view = skills.GetFunctionsView();
                display += $", Skills = {view.NativeFunctions.Count + view.SemanticFunctions.Count}";
            }

            display += $", Culture = {this.Culture.EnglishName}";

            return display;
        }
    }
}
