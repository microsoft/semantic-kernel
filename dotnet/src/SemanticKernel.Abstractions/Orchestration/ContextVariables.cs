// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Context Variables is a data structure that holds temporary data while a task is being performed.
/// It is accessed and manipulated by functions in the pipeline.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
[DebuggerTypeProxy(typeof(ContextVariables.TypeProxy))]
public sealed class ContextVariables : IEnumerable<KeyValuePair<string, string>>
{
    /// <summary>
    /// In the simplest scenario, the data is an input string, stored here.
    /// </summary>
    public string Input => this._variables[MainKey];

    /// <summary>
    /// Constructor for context variables.
    /// </summary>
    /// <param name="content">Optional value for the main variable of the context.</param>
    public ContextVariables(string? content = null)
    {
        this._variables[MainKey] = content ?? string.Empty;
    }

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    public ContextVariables Update(string? content)
    {
        this._variables[MainKey] = content ?? string.Empty;
        return this;
    }

    /// <summary>
    /// Updates all the local data with new data, merging the two datasets.
    /// Do not discard old data
    /// </summary>
    /// <param name="newData">New data to be merged</param>
    /// <param name="merge">Whether to merge and keep old data, or replace. False == discard old data.</param>
    /// <returns>The current instance</returns>
    public ContextVariables Update(ContextVariables newData, bool merge = true)
    {
        if (!object.ReferenceEquals(this, newData))
        {
            // If requested, discard old data and keep only the new one.
            if (!merge) { this._variables.Clear(); }

            foreach (KeyValuePair<string, string> varData in newData._variables)
            {
                this._variables[varData.Key] = varData.Value;
            }
        }

        return this;
    }

    /// <summary>
    /// This method allows to store additional data in the context variables, e.g. variables needed by functions in the
    /// pipeline. These "variables" are visible also to semantic functions using the "{{varName}}" syntax, allowing
    /// to inject more information into prompt templates.
    /// </summary>
    /// <param name="name">Variable name</param>
    /// <param name="value">Value to store. If the value is NULL the variable is deleted.</param>
    /// TODO: support for more complex data types, and plan for rendering these values into prompt templates.
    public void Set(string name, string? value)
    {
        Verify.NotNullOrWhiteSpace(name);
        if (value != null)
        {
            this._variables[name] = value;
        }
        else
        {
            this._variables.TryRemove(name, out _);
        }
    }

    /// <summary>
    /// Fetch a variable value from the context variables.
    /// </summary>
    /// <param name="name">Variable name</param>
    /// <param name="value">Value</param>
    /// <returns>Whether the value exists in the context variables</returns>
    /// TODO: provide additional method that returns the value without using 'out'.
    public bool Get(string name, out string value)
    {
        if (this._variables.TryGetValue(name, out value!)) { return true; }

        value = string.Empty;
        return false;
    }

    /// <summary>
    /// Array of all variables in the context variables.
    /// </summary>
    /// <param name="name">The name of the variable.</param>
    /// <returns>The value of the variable.</returns>
    public string this[string name]
    {
        get => this._variables[name];
        set => this._variables[name] = value;
    }

    /// <summary>
    /// Returns true if there is a variable with the given name
    /// </summary>
    /// <param name="key"></param>
    /// <returns>True if there is a variable with the given name, false otherwise</returns>
    public bool ContainsKey(string key)
    {
        return this._variables.ContainsKey(key);
    }

    /// <summary>
    /// Print the processed input, aka the current data after any processing occurred.
    /// </summary>
    /// <returns>Processed input, aka result</returns>
    public override string ToString()
    {
        return this.Input;
    }

    /// <summary>
    /// Get an enumerator that iterates through the context variables.
    /// </summary>
    /// <returns>An enumerator that iterates through the context variables</returns>
    public IEnumerator<KeyValuePair<string, string>> GetEnumerator()
    {
        return this._variables.GetEnumerator();
    }

    IEnumerator IEnumerable.GetEnumerator()
    {
        return this._variables.GetEnumerator();
    }

    /// <summary>
    /// Create a copy of the current instance with a copy of the internal data
    /// </summary>
    /// <returns>Copy of the current instance</returns>
    public ContextVariables Clone()
    {
        var clone = new ContextVariables();
        foreach (KeyValuePair<string, string> x in this._variables)
        {
            clone[x.Key] = x.Value;
        }

        return clone;
    }

    internal const string MainKey = "INPUT";

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    internal string DebuggerDisplay =>
        this._variables.TryGetValue(MainKey, out string input) && !string.IsNullOrEmpty(input) ?
            $"Variables = {this._variables.Count}, Input = {input}" :
            $"Variables = {this._variables.Count}";

    #region private ================================================================================

    /// <summary>
    /// Important: names are case insensitive
    /// </summary>
    private readonly ConcurrentDictionary<string, string> _variables = new(StringComparer.OrdinalIgnoreCase);

    private sealed class TypeProxy
    {
        private readonly ContextVariables _variables;

        public TypeProxy(ContextVariables variables) => _variables = variables;

        [DebuggerBrowsable(DebuggerBrowsableState.RootHidden)]
        public KeyValuePair<string, string>[] Items => _variables._variables.ToArray();
    }

    #endregion
}
