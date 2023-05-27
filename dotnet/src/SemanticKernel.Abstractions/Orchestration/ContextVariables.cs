// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Security;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Context Variables is a data structure that holds temporary data while a task is being performed.
/// It is accessed and manipulated by functions in the pipeline.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
[DebuggerTypeProxy(typeof(ContextVariables.TypeProxy))]
public sealed class ContextVariables : IEnumerable<KeyValuePair<string, TrustAwareString>>
{
    /// <summary>
    /// In the simplest scenario, the data is an input string, stored here.
    /// </summary>
    public TrustAwareString Input => this._variables[MainKey];

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
    /// TODO: support for more complex data types, and plan for rendering these values into prompt templates.
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
    public bool Get(string name, out string value)
    {
        var exists = this.Get(name, out TrustAwareString trustAwareValue);

        value = trustAwareValue.Value;

        return exists;
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
    /// Returns true if there is a variable with the given name
    /// </summary>
    /// <param name="key"></param>
    /// <returns>True if there is a variable with the given name, false otherwise</returns>
    public bool ContainsKey(string key)
    {
        return this._variables.ContainsKey(key);
    }

    /// <summary>
    /// True if all the stored variables have trusted content.
    /// </summary>
    /// <returns></returns>
    public bool IsAllTrusted()
    {
        return this._variables.Values.All(v => v.IsTrusted);
    }

    /// <summary>
    /// Make all the variables stored in the context untrusted.
    /// </summary>
    public void UntrustAll()
    {
        // Create a copy of the variables map iterator with ToList to avoid
        // iterating in the map while updating it
        foreach (var item in this._variables.ToList())
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
    public override string ToString()
    {
        return this.Input;
    }

    /// <summary>
    /// Get an enumerator that iterates through the context variables.
    /// </summary>
    /// <returns>An enumerator that iterates through the context variables</returns>
    public IEnumerator<KeyValuePair<string, TrustAwareString>> GetEnumerator()
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
        foreach (KeyValuePair<string, TrustAwareString> x in this._variables)
        {
            clone.Set(x.Key, x.Value);
        }

        return clone;
    }

    internal const string MainKey = "INPUT";

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    internal string DebuggerDisplay =>
        this._variables.TryGetValue(MainKey, out var input) && !string.IsNullOrEmpty(input.Value)
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
