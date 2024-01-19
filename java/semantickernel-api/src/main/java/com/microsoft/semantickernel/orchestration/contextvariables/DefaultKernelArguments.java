// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.contextvariables;

import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import javax.annotation.Nullable;
import reactor.util.annotation.NonNull;

/// <summary>
/// Context Variables is a data structure that holds temporary data while a task is being performed.
/// It is accessed and manipulated by functions in the pipeline.
/// </summary>
public class DefaultKernelArguments implements KernelArguments, WritableKernelArguments {

    private final CaseInsensitiveMap<ContextVariable<?>> variables;
    private final Map<String, PromptExecutionSettings> executionSettings;

    /// <summary>
    /// In the simplest scenario, the data is an input string, stored here.
    /// </summary>
    // public string Input => this._variables[MainKey];

    /// <summary>
    /// Constructor for context variables.
    /// </summary>
    /// <param name="content">Optional value for the main variable of the context.</param>
    public DefaultKernelArguments(@NonNull ContextVariable<?> content) {
        this.variables = new CaseInsensitiveMap<>();
        this.variables.put(MAIN_KEY, content);
        this.executionSettings = new HashMap<>();
    }

    public DefaultKernelArguments(
        Map<String, ContextVariable<?>> variables,
        Map<String, PromptExecutionSettings> executionSettings) {
        if (variables == null) {
            this.variables = new CaseInsensitiveMap<>();
        } else {
            this.variables = new CaseInsensitiveMap<>(variables);
        }

        if (executionSettings == null) {
            this.executionSettings = new HashMap<>();
        } else {
            this.executionSettings = new HashMap<>(executionSettings);
        }
    }

    public DefaultKernelArguments(
        Map<String, ContextVariable<?>> variables,
        @Nullable
        PromptExecutionSettings executionSettings) {
        this.variables = new CaseInsensitiveMap<>(variables);
        this.executionSettings = new HashMap<>();
        this.executionSettings.put(PromptExecutionSettings.DEFAULT_SERVICE_ID, executionSettings);
    }


    public DefaultKernelArguments() {
        this.variables = new CaseInsensitiveMap<>();
        this.executionSettings = new HashMap<>();
    }

    public DefaultKernelArguments(KernelArguments arguments) {
        this(arguments, new HashMap<>());
    }

    @Override
    public KernelArguments setVariable(@NonNull String key, @NonNull ContextVariable<?> content) {
        this.variables.put(key, content);
        return this;
    }

    @Override
    public KernelArguments setVariable(String key, Object content) {
        this.variables.put(key, ContextVariable.of(content));
        return this;
    }

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a
    // result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    @Override
    public KernelArguments update(@NonNull ContextVariable<?> content) {
        return setVariable(MAIN_KEY, content);
    }

    @Override
    public KernelArguments update(String content) {
        return null;
    }

    public DefaultKernelArguments update(@NonNull DefaultKernelArguments newData) {
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
    public DefaultKernelArguments update(@NonNull KernelArguments newData, boolean merge) {
        this.variables.putAll(newData);
        return this;
    }

    @Override
    public KernelArguments remove(String key) {
        variables.remove(key);
        return this;
    }

    @Override
    public WritableKernelArguments writableClone() {
        return new DefaultKernelArguments(variables, executionSettings);
    }

    @Override
    @Nullable
    public ContextVariable<?> getInput() {
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

    @Nullable
    @Override
    public <T> ContextVariable<T> get(String key, Class<T> clazz) {
        ContextVariable<?> value = variables.get(key);
        if (value == null) {
            return null;
        } else if (clazz.isAssignableFrom(value.getType().getClazz())) {
            return (ContextVariable<T>) value;
        }

        throw new IllegalArgumentException(
            String.format(
                "Variable %s is of type %s, but requested type is %s",
                key, value.getType().getClazz(), clazz));
    }

    @Nullable
    @Override
    public Map<String, PromptExecutionSettings> getExecutionSettings() {
        return executionSettings;
    }

    @Override
    public boolean isNullOrEmpty(String key) {
        return get(key) == null || get(key).isEmpty();
    }

    @Override
    @Nullable
    public ContextVariable<?> get(String key) {
        return variables.get(key);
    }

    @Override
    public int size() {
        return variables.size();
    }

    @Override
    public boolean isEmpty() {
        return variables.isEmpty();
    }

    @Override
    public boolean containsKey(Object key) {
        return variables.containsKey(key);
    }

    @Override
    public boolean containsValue(Object value) {
        return variables.containsValue(value);
    }

    @Override
    public ContextVariable<?> get(Object key) {
        return variables.get(key);
    }

    @Override
    public ContextVariable<?> put(String key, ContextVariable<?> value) {
        return variables.put(key, value);
    }

    @Override
    public ContextVariable<?> remove(Object key) {
        return variables.remove(key);
    }

    @Override
    public void putAll(Map<? extends String, ? extends ContextVariable<?>> m) {
        variables.putAll(m);
    }

    @Override
    public void clear() {
        variables.clear();
    }

    @Override
    public Set<String> keySet() {
        return variables.keySet();
    }

    @Override
    public Collection<ContextVariable<?>> values() {
        return variables.values();
    }

    @Override
    public Set<Entry<String, ContextVariable<?>>> entrySet() {
        return variables.entrySet();
    }


    public static class Builder implements KernelArguments.Builder {

        private final DefaultKernelArguments variables;
        private final Map<String, PromptExecutionSettings> executionSettings;

        public Builder() {
            variables = new DefaultKernelArguments();
            this.variables.put(MAIN_KEY, ContextVariable.of(""));

            executionSettings = new HashMap<>();
        }

        @Override
        public <T> KernelArguments.Builder withVariable(String key, ContextVariable<T> value) {
            variables.put(key, value);
            return this;
        }

        @Override
        public KernelArguments.Builder withVariable(String key, Object value) {
            variables.put(key, ContextVariable.of(value));
            return this;
        }

        @Override
        public <T> Builder withInput(ContextVariable<T> content) {
            variables.put(MAIN_KEY, content);
            return this;
        }

        @Override
        public KernelArguments.Builder withInput(Object content) {
            return withInput(ContextVariable.of(content));
        }

        @Override
        public Builder withVariables(Map<String, ContextVariable<?>> map) {
            variables.putAll(map);
            return this;
        }

        @Override
        public KernelArguments build() {
            return new DefaultKernelArguments(variables, executionSettings);
        }
    }
}
