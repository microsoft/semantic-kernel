// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Context Variables is a data structure that holds temporary data while a task is being performed.
/// It is accessed and manipulated by functions in the pipeline.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
[DebuggerTypeProxy(typeof(ContextVariables.TypeProxy))]
public sealed class ContextVariables : Dictionary<string, string>
{
    /// <summary>
    /// Constructor for context variables.
    /// </summary>
    /// <param name="value">Optional value for the main variable of the context including trust information.</param>
    public ContextVariables(string? value = null)
        : base(StringComparer.OrdinalIgnoreCase)
    {
        this.Set(MainKey, value);
    }

    /// <summary>
    /// Create a copy of the current instance with a copy of the internal data
    /// </summary>
    /// <returns>Copy of the current instance</returns>
    public ContextVariables Clone()
    {
        var clone = new ContextVariables();
        foreach (KeyValuePair<string, string> x in this)
        {
            clone.Set(x.Key, x.Value);
        }

        return clone;
    }

    /// <summary>Gets the main input string.</summary>
    /// <remarks>If the main input string was removed from the collection, an empty string will be returned.</remarks>
    public string Input => this.TryGetValue(MainKey, out string? value) ? value : string.Empty;

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="value">The new input value, for the next function in the pipeline, or as a result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    public ContextVariables Update(string? value)
    {
        this.Set(MainKey, value);
        return this;
    }

    /// <summary>
    /// This method allows to store additional data in the context variables, e.g. variables needed by functions in the
    /// pipeline. These "variables" are visible also to semantic functions using the "{{varName}}" syntax, allowing
    /// to inject more information into prompt templates.
    /// </summary>
    /// <param name="name">Variable name</param>
    /// <param name="value">Value to store. If the value is NULL the variable is deleted.</param>
    public void Set(string name, string? value)
    {
        Verify.NotNullOrWhiteSpace(name);
        if (value != null)
        {
            this[name] = value;
        }
        else
        {
            this.Remove(name);
        }
    }

    /// <summary>
    /// Print the processed input, aka the current data after any processing occurred.
    /// </summary>
    /// <returns>Processed input, aka result</returns>
    public override string ToString() => this.Input;

    internal const string MainKey = "INPUT";

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    internal string DebuggerDisplay =>
        this.TryGetValue(MainKey, out string? input) && !string.IsNullOrEmpty(input)
            ? $"Variables = {this.Count}, Input = {input}"
            : $"Variables = {this.Count}";

    #region private ================================================================================

    private sealed class TypeProxy
    {
        private readonly ContextVariables _variables;

        public TypeProxy(ContextVariables variables) => this._variables = variables;

        [DebuggerBrowsable(DebuggerBrowsableState.RootHidden)]
        public KeyValuePair<string, string>[] Items => this._variables.ToArray();
    }

    #endregion
}
