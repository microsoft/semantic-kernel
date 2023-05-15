// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

// Copyright (c) Microsoft. All rights reserved.

import reactor.util.annotation.NonNull;

import java.util.Map;

import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

/**
 * Context Variables is a data structure that holds temporary data while a task is being performed.
 * It is accessed by functions in the pipeline.
 */
public interface ContextVariables {

    String MAIN_KEY = "input";

    Map<String, String> asMap();

    @CheckReturnValue
    ContextVariables copy();

    /**
     * Set the value
     *
     * @param key variable name
     * @param content value to set
     * @return Contect for fluent calls
     */
    ContextVariables setVariable(@NonNull String key, @NonNull String content);

    interface Builder {
        ContextVariables build();

        /**
         * Builds an instance with the given content in the default main key
         *
         * @param content Entry to place in the "input" slot
         * @return an instantiation of ContextVariables
         */
        ContextVariables build(String content);
    }

    /**
     * Return the variable with the given name
     *
     * @param key variable name
     * @return content of the variable
     */
    @Nullable
    String get(String key);

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
