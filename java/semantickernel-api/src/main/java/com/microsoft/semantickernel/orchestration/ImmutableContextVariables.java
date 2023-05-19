// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

// Copyright (c) Microsoft. All rights reserved.

import reactor.util.annotation.NonNull;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

/// <summary>
/// Context Variables is a data structure that holds temporary data while a task is being performed.
/// It is accessed and manipulated by functions in the pipeline.
/// </summary>
class ImmutableContextVariables implements ReadOnlyContextVariables {

    // TODO case insensitive
    private final Map<String, String> variables;

    /// <summary>
    /// In the simplest scenario, the data is an input string, stored here.
    /// </summary>
    // public string Input => this._variables[MainKey];

    /// <summary>
    /// Constructor for context variables.
    /// </summary>
    /// <param name="content">Optional value for the main variable of the context.</param>
    ImmutableContextVariables(@NonNull String content) {
        this.variables = new HashMap<>();
        this.variables.put(MAIN_KEY, content);
    }

    ImmutableContextVariables(Map<String, String> variables) {
        this.variables = new HashMap<>(variables);
    }

    @CheckReturnValue
    ImmutableContextVariables setVariable(@NonNull String key, @NonNull String content) {
        HashMap<String, String> copy = new HashMap<>(this.variables);
        copy.put(key, content);
        return new ImmutableContextVariables(copy);
    }

    @CheckReturnValue
    ImmutableContextVariables appendToVariable(@NonNull String key, @NonNull String content) {
        return setVariable(key, this.variables.get(key) + content);
    }

    @Override
    public Map<String, String> getVariables() {
        return Collections.unmodifiableMap(variables);
    }

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a
    // result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    @CheckReturnValue
    public ImmutableContextVariables update(@NonNull String content) {
        return setVariable(MAIN_KEY, content);
    }

    @CheckReturnValue
    public ImmutableContextVariables update(@NonNull ImmutableContextVariables newData) {
        return update(newData, true);
    }

    /// <summary>
    /// Updates all the local data with new data, merging the two datasets.
    /// Do not discard old data
    /// </summary>
    /// <param name="newData">New data to be merged</param>
    /// <param name="merge">Whether to merge and keep old data, or replace. False == discard old
    // data.</param>
    /// <returns>The current instance</returns>

    @CheckReturnValue
    public ImmutableContextVariables update(
            @NonNull ReadOnlyContextVariables newData, boolean merge) {
        /*
        // If requested, discard old data and keep only the new one.
        if (!merge) { this._variables.Clear(); }

        foreach (KeyValuePair<string, string> varData in newData._variables)
        {
            this._variables[varData.Key] = varData.Value;
        }

         */
        HashMap<String, String> clone = new HashMap<>(this.variables);
        if (!merge) {
            clone.clear();
        }
        clone.putAll(newData.getVariables());

        return new ImmutableContextVariables(clone);
    }

    @CheckReturnValue
    @Override
    public ImmutableContextVariables copy() {
        return new ImmutableContextVariables(variables);
    }

    @Override
    @Nullable
    public String get(String key) {
        return variables.get(key);
    }
    /*

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
        Verify.NotEmpty(name, "The variable name is empty");
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

    #region private ================================================================================

    private const string MainKey = "INPUT";

    // Important: names are case insensitive
    private readonly ConcurrentDictionary<string, string> _variables = new(StringComparer.InvariantCultureIgnoreCase);

    #endregion

     */
}
