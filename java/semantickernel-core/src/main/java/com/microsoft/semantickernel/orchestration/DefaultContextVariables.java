// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.skilldefinition.CaseInsensitiveMap;
import java.util.Collections;
import java.util.Map;
import javax.annotation.Nullable;
import reactor.util.annotation.NonNull;

/// <summary>
/// Context Variables is a data structure that holds temporary data while a task is being performed.
/// It is accessed and manipulated by functions in the pipeline.
/// </summary>
class DefaultContextVariables implements ContextVariables, WritableContextVariables {

    private final CaseInsensitiveMap<Object> variables;

    /// <summary>
    /// In the simplest scenario, the data is an input string, stored here.
    /// </summary>
    // public string Input => this._variables[MainKey];

    /// <summary>
    /// Constructor for context variables.
    /// </summary>
    /// <param name="content">Optional value for the main variable of the context.</param>
    DefaultContextVariables(@NonNull Object content) {
        this.variables = new CaseInsensitiveMap<>();
        this.variables.put(MAIN_KEY, content);
    }

    DefaultContextVariables(Map<String, Object> variables) {
        this.variables = new CaseInsensitiveMap<>(variables);
    }

    @Override
    public ContextVariables setVariable(@NonNull String key, @NonNull Object content) {
        this.variables.put(key, content);
        return this;
    }

    @Override
    public Map<String, Object> asMap() {
        return Collections.unmodifiableMap(variables);
    }

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a
    // result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    @Override
    public ContextVariables update(@NonNull Object content) {
        return setVariable(MAIN_KEY, content);
    }

    public DefaultContextVariables update(@NonNull DefaultContextVariables newData) {
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
    @Override
    public DefaultContextVariables update(@NonNull ContextVariables newData, boolean merge) {
        /*
        // If requested, discard old data and keep only the new one.
        if (!merge) { this._variables.Clear(); }

        foreach (KeyValuePair<string, string> varData in newData._variables)
        {
            this._variables[varData.Key] = varData.Value;
        }

         */
        this.variables.putAll(newData.asMap());
        return this;
    }

    @Override
    public ContextVariables remove(String key) {
        variables.remove(key);
        return this;
    }

    @Override
    public WritableContextVariables writableClone() {
        return new DefaultContextVariables(variables);
    }

    @Override
    @Nullable
    public Object getInput() {
        return get(MAIN_KEY);
    }

    @Override
    public String prettyPrint() {
        return variables.entrySet().stream()
                .reduce(
                        "",
                        (str, entry) ->
                                str
                                        + System.lineSeparator()
                                        + entry.getKey()
                                        + ": "
                                        + entry.getValue(),
                        (a, b) -> a + b);
    }

    @Override
    @Nullable
    public Object get(String key) {
        return variables.get(key);
    }

    public static class WritableBuilder implements WritableContextVariables.Builder {
        @Override
        public WritableContextVariables build(Map<String, Object> map) {
            return new DefaultContextVariables(map);
        }
    }

    public static class Builder implements ContextVariables.Builder {

        private final Map<String, Object> variables;

        public Builder() {
            variables = new CaseInsensitiveMap<>();
//            this.variables.put(MAIN_KEY, "");
        }

        @Override
        public ContextVariables.Builder withVariable(String key, Object value) {
            variables.put(key, value);
            return this;
        }

        @Override
        public Builder withInput(String content) {
            variables.put(MAIN_KEY, content);
            return this;
        }

        @Override
        public Builder withVariables(Map<String, Object> map) {
            variables.putAll(map);
            return this;
        }

        @Override
        public ContextVariables build() {
            return new DefaultContextVariables(variables);
        }
    }
}
