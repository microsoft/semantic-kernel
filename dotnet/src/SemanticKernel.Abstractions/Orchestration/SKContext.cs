// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Semantic Kernel context.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public abstract class SKContext
{
    /// <summary>
    /// Print the processed input, aka the current data after any processing occurred.
    /// </summary>
    /// <returns>Processed input, aka result</returns>
    public virtual string Result => this.Variables.ToString();

    /// <summary>
    /// When a prompt is processed, aka the current data after any model results processing occurred.
    /// (One prompt can have multiple results).
    /// </summary>
    public abstract IReadOnlyList<ModelResult> ModelResults { get; set; }

    /// <summary>
    /// The culture currently associated with this context.
    /// </summary>
    public abstract CultureInfo Culture { get; }

    /// <summary>
    /// User variables
    /// </summary>
    public abstract ContextVariables Variables { get; }

    /// <summary>
    /// Read only skills collection
    /// </summary>
    public abstract IReadOnlySkillCollection Skills { get; }

    /// <summary>
    /// App logger
    /// </summary>
    public abstract ILogger Logger { get; }

    /// <summary>
    /// Creates a clone of the current context
    /// </summary>
    /// <returns>A new context copied from the current one</returns>
    public abstract SKContext Clone();

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay
    {
        get
        {
            if (this.ErrorOccurred)
            {
                return $"Error: {this.LastException?.Message}";
            }

            string display = this.Variables.DebuggerDisplay;

            if (this.Skills is IReadOnlySkillCollection skills)
            {
                var view = skills.GetFunctionsView();
                display += $", Skills = {view.NativeFunctions.Count + view.SemanticFunctions.Count}";
            }

            display += $", Culture = {this.Culture.EnglishName}";
            display += $", Culture = {this.Culture.EnglishName}";
            return display;
        }
    }

    #region Error handling
    /// <summary>
    /// Whether an error occurred while executing functions in the pipeline.
    /// </summary>
    public abstract bool ErrorOccurred { get; }

    /// <summary>
    /// When an error occurs, this is the most recent exception.
    /// </summary>
    public abstract Exception? LastException { get; }
    #endregion

    #region Obsolete
    /// <summary>
    /// Shortcut into user data, access variables by name
    /// </summary>
    /// <param name="name">Variable name</param>
    [Obsolete("Use SKContext.Variables instead. This property will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public string this[string name]
    {
        get => this.Variables[name];
        set => this.Variables[name] = value;
    }

    /// <summary>
    /// App logger (obsolete - use 'Logger' instead).
    /// </summary>
    [Obsolete("Use SKContext.Logger instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ILogger Log
        => this.Logger;

    /// <summary>
    /// The token to monitor for cancellation requests.
    /// </summary>
    [Obsolete("Add a CancellationToken param to SKFunction method signatures instead of retrieving it from SKContext.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public CancellationToken CancellationToken
        => default;

    /// <summary>
    /// Semantic memory
    /// </summary>
    [Obsolete("Memory no longer passed through SKContext. Instead, initialize your skill class with the memory provider it needs.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISemanticTextMemory Memory
        => throw new InvalidOperationException(
            "Memory no longer passed through SKContext. Instead, initialize your skill class with the memory provider it needs.");

    /// <summary>
    /// Error details.
    /// </summary>
    [Obsolete("Use LastException.Message instead. This property will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public string? LastErrorDescription => this.LastException?.Message;

    /// <summary>
    /// Call this method to signal when an error occurs.
    /// In the usual scenarios this is also how execution is stopped, e.g. to inform the user or take necessary steps.
    /// </summary>
    /// <param name="errorDescription">Error description</param>
    /// <param name="exception">If available, the exception occurred</param>
    /// <returns>The current instance</returns>
    [Obsolete("Throw exception from SKFunction implementation instead. The Kernel will set the failure properties. " +
        "This method will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public abstract SKContext Fail(string errorDescription, Exception? exception = null);

    /// <summary>
    /// Access registered functions by skill + name. Not case sensitive.
    /// The function might be native or semantic, it's up to the caller handling it.
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>Delegate to execute the function</returns>
    [Obsolete("Use SKContext.Skills.GetFunction(skillName, functionName) instead. " +
    "This method will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISKFunction Func(string skillName, string functionName) =>
        this.Skills.GetFunction(skillName, functionName);
    #endregion
}
