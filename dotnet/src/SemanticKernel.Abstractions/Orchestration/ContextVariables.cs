// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Security;

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
public sealed class ContextVariables : IDictionary<string, TrustAwareString>
{
    /// <summary>
    /// Constructor for context variables.
    /// </summary>
    /// <param name="trustAwareContent">Optional value for the main variable of the context including trust information.</param>
    public ContextVariables(TrustAwareString? trustAwareContent = null)
    {
        this._variables[MainKey] = trustAwareContent ?? TrustAwareString.Empty;
    }

    /// <summary>
    /// Constructor for context variables.
    /// By default the content will be trusted.
    /// </summary>
    /// <param name="content">Optional value for the main variable of the context.</param>
    public ContextVariables(string? content) : this(TrustAwareString.CreateTrusted(content)) { }

    /// <summary>
    /// Create a copy of the current instance with a copy of the internal data
    /// </summary>
    /// <returns>Copy of the current instance</returns>
    public ContextVariables Clone()
    {
        var clone = new ContextVariables();
        foreach (KeyValuePair<string, TrustAwareString> x in this._variables)
        {
            clone.Set(x.Key, x.Value);
        }

        return clone;
    }

    /// <summary>Gets the main input string.</summary>
    /// <remarks>If the main input string was removed from the collection, an empty string will be returned.</remarks>
    public TrustAwareString Input => this._variables.TryGetValue(MainKey, out TrustAwareString? value) ? value : TrustAwareString.Empty;

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// The string includes trust information and will overwrite the trust state of the input.
    /// </summary>
    /// <param name="trustAwareContent">The new input value, for the next function in the pipeline, or as a result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    public ContextVariables Update(TrustAwareString? trustAwareContent)
    {
        this._variables[MainKey] = trustAwareContent ?? TrustAwareString.Empty;
        return this;
    }

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// By default the content will be trusted.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    public ContextVariables Update(string? content)
    {
        return this.Update(TrustAwareString.CreateTrusted(content));
    }

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// This will keep the trust state of the current input set.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    public ContextVariables UpdateKeepingTrustState(string? content)
    {
        return this.Update(new TrustAwareString(content, this.Input.IsTrusted));
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

            foreach (KeyValuePair<string, TrustAwareString> varData in newData._variables)
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
    /// <param name="trustAwareValue">Value to store. If the value is NULL the variable is deleted.</param>
    public void Set(string name, TrustAwareString? trustAwareValue)
    {
        Verify.NotNullOrWhiteSpace(name);
        if (trustAwareValue != null)
        {
            this._variables[name] = trustAwareValue;
        }
        else
        {
            this._variables.TryRemove(name, out _);
        }
    }

    /// <summary>
    /// This method allows to store additional data in the context variables, e.g. variables needed by functions in the
    /// pipeline. These "variables" are visible also to semantic functions using the "{{varName}}" syntax, allowing
    /// to inject more information into prompt templates.
    /// By default the variables' value will be trusted.
    /// </summary>
    /// <param name="name">Variable name</param>
    /// <param name="value">Value to store</param>
    public void Set(string name, string value)
    {
        this.Set(name, TrustAwareString.CreateTrusted(value));
    }

    /// <summary>
    /// Fetch a variable value and if its content is trusted from the context variables.
    /// </summary>
    /// <param name="name">Variable name</param>
    /// <param name="trustAwareValue">Variable value as a string with trust information</param>
    /// <returns>Whether the value exists in the context variables</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Use the TryGetValue method or indexer instead.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public bool Get(string name, out TrustAwareString trustAwareValue)
    {
        if (this._variables.TryGetValue(name, out TrustAwareString result))
        {
            trustAwareValue = result;
            return true;
        }

        trustAwareValue = TrustAwareString.Empty;
        return false;
    }

    /// <summary>
    /// Fetch a variable value from the context variables.
    /// </summary>
    /// <param name="name">Variable name</param>
    /// <param name="value">Value</param>
    /// <returns>Whether the value exists in the context variables</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Use the TryGetValue method or indexer instead.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public bool Get(string name, out string value)
    {
        var exists = this.Get(name, out TrustAwareString trustAwareValue);

        value = trustAwareValue.Value;

        return exists;
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
    public bool TryGetValue(string name, [NotNullWhen(true)] out TrustAwareString? value) =>
        this._variables.TryGetValue(name, out value);

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
        if (this._variables.TryGetValue(name, out TrustAwareString? trustAwareValue))
        {
            value = trustAwareValue.Value;
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
        get => this._variables[name].Value;
        set
        {
            // This will be trusted by default for now.
            // TODO: we could plan to replace string usages in the kernel
            // with TrustAwareString, so here "value" could directly be a trust aware string
            // including trust information
            this._variables[name] = TrustAwareString.CreateTrusted(value);
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
    /// True if all the stored variables have trusted content.
    /// </summary>
    /// <returns></returns>
    public bool IsAllTrusted()
    {
        foreach (var pair in this._variables)
        {
            if (!pair.Value.IsTrusted)
            {
                return false;
            }
        }
        return true;
    }

    /// <summary>
    /// Make all the variables stored in the context untrusted.
    /// </summary>
    public void UntrustAll()
    {
        foreach (var item in this._variables)
        {
            // Note: we don't use an internal setter for better multi-threading
            this._variables[item.Key] = TrustAwareString.CreateUntrusted(item.Value.Value);
        }
    }

    /// <summary>
    /// Make the input variable untrusted.
    /// </summary>
    public void UntrustInput()
    {
        this.Update(TrustAwareString.CreateUntrusted(this.Input.Value));
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
    public IEnumerator<KeyValuePair<string, TrustAwareString>> GetEnumerator() => this._variables.GetEnumerator();

    IEnumerator IEnumerable.GetEnumerator() => this._variables.GetEnumerator();
    void IDictionary<string, TrustAwareString>.Add(string key, TrustAwareString value) => ((IDictionary<string, TrustAwareString>)this._variables).Add(key, value);
    bool IDictionary<string, TrustAwareString>.Remove(string key) => ((IDictionary<string, TrustAwareString>)this._variables).Remove(key);
    void ICollection<KeyValuePair<string, TrustAwareString>>.Add(KeyValuePair<string, TrustAwareString> item) => ((ICollection<KeyValuePair<string, TrustAwareString>>)this._variables).Add(item);
    void ICollection<KeyValuePair<string, TrustAwareString>>.Clear() => ((ICollection<KeyValuePair<string, TrustAwareString>>)this._variables).Clear();
    bool ICollection<KeyValuePair<string, TrustAwareString>>.Contains(KeyValuePair<string, TrustAwareString> item) => ((ICollection<KeyValuePair<string, TrustAwareString>>)this._variables).Contains(item);
    void ICollection<KeyValuePair<string, TrustAwareString>>.CopyTo(KeyValuePair<string, TrustAwareString>[] array, int arrayIndex) => ((ICollection<KeyValuePair<string, TrustAwareString>>)this._variables).CopyTo(array, arrayIndex);
    bool ICollection<KeyValuePair<string, TrustAwareString>>.Remove(KeyValuePair<string, TrustAwareString> item) => ((ICollection<KeyValuePair<string, TrustAwareString>>)this._variables).Remove(item);
    ICollection<string> IDictionary<string, TrustAwareString>.Keys => ((IDictionary<string, TrustAwareString>)this._variables).Keys;
    ICollection<TrustAwareString> IDictionary<string, TrustAwareString>.Values => ((IDictionary<string, TrustAwareString>)this._variables).Values;
    int ICollection<KeyValuePair<string, TrustAwareString>>.Count => ((ICollection<KeyValuePair<string, TrustAwareString>>)this._variables).Count;
    bool ICollection<KeyValuePair<string, TrustAwareString>>.IsReadOnly => ((ICollection<KeyValuePair<string, TrustAwareString>>)this._variables).IsReadOnly;
    TrustAwareString IDictionary<string, TrustAwareString>.this[string key]
    {
        get => ((IDictionary<string, TrustAwareString>)this._variables)[key];
        set => ((IDictionary<string, TrustAwareString>)this._variables)[key] = value;
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
    private readonly ConcurrentDictionary<string, TrustAwareString> _variables = new(StringComparer.OrdinalIgnoreCase);

    private sealed class TypeProxy
    {
        private readonly ContextVariables _variables;

        public TypeProxy(ContextVariables variables) => this._variables = variables;

        [DebuggerBrowsable(DebuggerBrowsableState.RootHidden)]
        public KeyValuePair<string, TrustAwareString>[] Items => this._variables._variables.ToArray();
    }

    #endregion
}
