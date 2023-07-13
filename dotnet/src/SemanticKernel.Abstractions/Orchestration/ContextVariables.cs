// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable CA1710 // ContextVariables doesn't end in Dictionary or Collection
#pragma warning disable CA1725, RCS1168 // Uses "name" instead of "key" for some public APIs
#pragma warning disable CS8767 // Reference type nullability doesn't match because netstandard2.0 surface area isn't nullable reference type annotated
// TODO: support more complex data types, and plan for rendering these values into prompt templates.

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Context Variables is a data structure that holds temporary data while a task is being performed.
/// It is accessed and manipulated by functions in the pipeline.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
[DebuggerTypeProxy(typeof(ContextVariables.TypeProxy))]
public sealed class ContextVariables : IDictionary<string, string>
{
    /// <summary>
    /// Constructor for context variables.
    /// </summary>
    /// <param name="value">Optional value for the main variable of the context including trust information.</param>
    public ContextVariables(string? value = null)
    {
        this._variables[MainKey] = value ?? string.Empty;
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
            clone.Set(x.Key, x.Value);
        }

        return clone;
    }

    /// <summary>Gets the main input string.</summary>
    /// <remarks>If the main input string was removed from the collection, an empty string will be returned.</remarks>
    public string Input => this._variables.TryGetValue(MainKey, out string? value) ? value : string.Empty;

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// The string includes trust information and will overwrite the trust state of the input.
    /// </summary>
    /// <param name="value">The new input value, for the next function in the pipeline, or as a result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    public ContextVariables Update(string? value)
    {
        this._variables[MainKey] = value ?? string.Empty;
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
    /// The string value includes trust information and will overwrite the trust information already stored for the variable.
    /// </summary>
    /// <param name="name">Variable name</param>
    /// <param name="value">Value to store. If the value is NULL the variable is deleted.</param>
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
    /// Gets the variable value associated with the specified name.
    /// </summary>
    /// <param name="name">The name of the variable to get.</param>
    /// <param name="value">
    /// When this method returns, contains the variable value associated with the specified name, if the variable is found;
    /// otherwise, null.
    /// </param>
    /// <returns>true if the <see cref="ContextVariables"/> contains a variable with the specified name; otherwise, false.</returns>
    public bool TryGetValue(string name, [NotNullWhen(true)] out string? value)
    {
        if (this._variables.TryGetValue(name, out value))
        {
            return true;
        }

        value = null;
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
        set
        {
            this._variables[name] = value;
        }
    }

    /// <summary>
    /// Determines whether the <see cref="ContextVariables"/> contains the specified variable.
    /// </summary>
    /// <param name="name">The name of the variable to locate.</param>
    /// <returns>true if the <see cref="ContextVariables"/> contains a variable with the specified name; otherwise, false.</returns>
    public bool ContainsKey(string name)
    {
        return this._variables.ContainsKey(name);
    }

    /// <summary>
    /// Print the processed input, aka the current data after any processing occurred.
    /// </summary>
    /// <returns>Processed input, aka result</returns>
    public override string ToString() => this.Input;

    /// <summary>
    /// Get an enumerator that iterates through the context variables.
    /// </summary>
    /// <returns>An enumerator that iterates through the context variables</returns>
    public IEnumerator<KeyValuePair<string, string>> GetEnumerator() => this._variables.GetEnumerator();

    IEnumerator IEnumerable.GetEnumerator() => this._variables.GetEnumerator();
    void IDictionary<string, string>.Add(string key, string value) => ((IDictionary<string, string>)this._variables).Add(key, value);
    bool IDictionary<string, string>.Remove(string key) => ((IDictionary<string, string>)this._variables).Remove(key);
    void ICollection<KeyValuePair<string, string>>.Add(KeyValuePair<string, string> item) => ((ICollection<KeyValuePair<string, string>>)this._variables).Add(item);
    void ICollection<KeyValuePair<string, string>>.Clear() => ((ICollection<KeyValuePair<string, string>>)this._variables).Clear();
    bool ICollection<KeyValuePair<string, string>>.Contains(KeyValuePair<string, string> item) => ((ICollection<KeyValuePair<string, string>>)this._variables).Contains(item);
    void ICollection<KeyValuePair<string, string>>.CopyTo(KeyValuePair<string, string>[] array, int arrayIndex) => ((ICollection<KeyValuePair<string, string>>)this._variables).CopyTo(array, arrayIndex);
    bool ICollection<KeyValuePair<string, string>>.Remove(KeyValuePair<string, string> item) => ((ICollection<KeyValuePair<string, string>>)this._variables).Remove(item);
    ICollection<string> IDictionary<string, string>.Keys => ((IDictionary<string, string>)this._variables).Keys;
    ICollection<string> IDictionary<string, string>.Values => ((IDictionary<string, string>)this._variables).Values;
    int ICollection<KeyValuePair<string, string>>.Count => ((ICollection<KeyValuePair<string, string>>)this._variables).Count;
    bool ICollection<KeyValuePair<string, string>>.IsReadOnly => ((ICollection<KeyValuePair<string, string>>)this._variables).IsReadOnly;
    string IDictionary<string, string>.this[string key]
    {
        get => ((IDictionary<string, string>)this._variables)[key];
        set => ((IDictionary<string, string>)this._variables)[key] = value;
    }

    internal const string MainKey = "INPUT";

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    internal string DebuggerDisplay =>
        this.TryGetValue(MainKey, out string? input) && !string.IsNullOrEmpty(input)
            ? $"Variables = {this._variables.Count}, Input = {input}"
            : $"Variables = {this._variables.Count}";

    #region private ================================================================================

    /// <summary>
    /// Important: names are case insensitive
    /// </summary>
    private readonly ConcurrentDictionary<string, string> _variables = new(StringComparer.OrdinalIgnoreCase);

    private sealed class TypeProxy
    {
        private readonly ContextVariables _variables;

        public TypeProxy(ContextVariables variables) => this._variables = variables;

        [DebuggerBrowsable(DebuggerBrowsableState.RootHidden)]
        public KeyValuePair<string, string>[] Items => this._variables._variables.ToArray();
    }

    #endregion
}
