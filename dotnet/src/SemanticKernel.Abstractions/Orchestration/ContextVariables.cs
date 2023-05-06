// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Context Variables is a data structure that holds temporary data while a task is being performed.
/// It is accessed and manipulated by functions in the pipeline.
/// </summary>
public sealed class ContextVariables : IEnumerable<KeyValuePair<string, string>>
{
    /// <summary>
    /// In the simplest scenario, the data is an input string, stored here.
    /// </summary>
    public string Input => this.TryGet(MainKey, out var value) ? value : string.Empty;

    /// <summary>
    /// Constructor for context variables.
    /// </summary>
    /// <param name="content">Optional value for the main variable of the context.</param>
    public ContextVariables(string? content = null)
    {
        this.Set(MainKey, content);
    }

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    public ContextVariables Update(string? content)
    {
        this.Set(MainKey, content);
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
            if (!merge && this._variables.IsValueCreated) { this._variables.Value.Clear(); }

            foreach (KeyValuePair<string, string> varData in newData)
            {
                this.Set(varData.Key, varData.Value);
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
    /// <param name="value">Value to store. If the value is null or empty, the variable is deleted.</param>
    /// TODO: support for more complex data types, and plan for rendering these values into prompt templates.
    public void Set(string name, string? value)
    {
        Verify.NotNullOrWhiteSpace(name);
        if (!string.IsNullOrEmpty(value))
        {
            this._variables.Value[name] = value!;
        }
        else if (this._variables.IsValueCreated)
        {
            _ = this._variables.Value.Remove(name);
        }
    }

    /// <summary>
    /// Fetch a variable value from the context variables.
    /// </summary>
    /// <param name="name">Variable name</param>
    /// <param name="value">Value</param>
    /// <returns>Whether the value exists in the context variables</returns>
    /// TODO: provide additional method that returns the value without using 'out'.
    public bool TryGet(string name, out string value)
    {
        value = string.Empty;
        return this._variables.IsValueCreated && this._variables.Value.TryGetValue(name, out value);
    }

    /// <summary>
    /// Array of all variables in the context variables.
    /// </summary>
    /// <param name="name">The name of the variable.</param>
    /// <returns>The value of the variable.</returns>
    public string this[string name]
    {
        get => this.TryGet(name, out string value) ? value
                : throw new KeyNotFoundException($"Key not found in ContextVariables: {name}");

        set => this.Set(name, value);
    }

    /// <summary>
    /// Returns true if there is a variable with the given name
    /// </summary>
    /// <param name="key"></param>
    /// <returns>True if there is a variable with the given name, false otherwise</returns>
    public bool ContainsKey(string key)
    {
        return this._variables.IsValueCreated && this._variables.Value.ContainsKey(key);
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
        return this._variables.IsValueCreated ? this._variables.Value.GetEnumerator()
            : Enumerable.Empty<KeyValuePair<string, string>>().GetEnumerator();
    }

    IEnumerator IEnumerable.GetEnumerator()
    {
        return this.GetEnumerator();
    }

    /// <summary>
    /// Create a copy of the current instance with a copy of the internal data
    /// </summary>
    /// <returns>Copy of the current instance</returns>
    public ContextVariables Clone()
    {
        var clone = new ContextVariables();
        if (this._variables.IsValueCreated)
        {
            foreach (KeyValuePair<string, string> x in this._variables.Value)
            {
                clone[x.Key] = x.Value;
            }
        }


        return clone;
    }

    internal const string MainKey = "INPUT";

    #region private ================================================================================

    // Important: names are case insensitive
    private readonly Lazy<Dictionary<string, string>> _variables = new(() => new (StringComparer.OrdinalIgnoreCase));

    #endregion
}
