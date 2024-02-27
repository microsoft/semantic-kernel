// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.exceptions.SKException;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import javax.annotation.Nullable;
import reactor.util.annotation.NonNull;

/**
 * Arguments to a kernel function.
 */
public class KernelFunctionArguments implements Buildable, Map<String, ContextVariable<?>> {

    /**
     * Default key for the main input.
     */
    public static final String MAIN_KEY = "input";

    private final CaseInsensitiveMap<ContextVariable<?>> variables;

    /**
     * Create a new instance of KernelFunctionArguments.
     *
     * @param variables The variables to use for the function invocation.
     */
    protected KernelFunctionArguments(
        @Nullable Map<String, ContextVariable<?>> variables) {
        if (variables == null) {
            this.variables = new CaseInsensitiveMap<>();
        } else {
            this.variables = new CaseInsensitiveMap<>(variables);
        }
    }

    /**
     * Create a new instance of KernelFunctionArguments.
     *
     * @param content The content to use for the function invocation.
     */
    protected KernelFunctionArguments(@NonNull ContextVariable<?> content) {
        this.variables = new CaseInsensitiveMap<>();
        this.variables.put(MAIN_KEY, content);
    }

    /**
     * Create a new instance of KernelFunctionArguments.
     */
    protected KernelFunctionArguments() {
        this.variables = new CaseInsensitiveMap<>();
    }

    /**
     * Create a new instance of Builder.
     *
     * @return Builder
     */
    public static Builder builder() {
        return new KernelFunctionArguments.Builder();
    }

    /**
     * Get the input (entry in the MAIN_KEY slot)
     *
     * @return input
     */
    @Nullable
    public ContextVariable<?> getInput() {
        return get(MAIN_KEY);
    }

    /**
     * Create formatted string of the variables
     *
     * @return formatted string
     */
    public String prettyPrint() {
        return variables.entrySet().stream()
            .reduce(
                "",
                (str, entry) -> str
                    + System.lineSeparator()
                    + entry.getKey()
                    + ": "
                    + entry.getValue(),
                (a, b) -> a + b);
    }

    /**
     * Return the variable with the given name
     *
     * @param key variable name
     * @return content of the variable
     */
    @Nullable
    public ContextVariable<?> get(String key) {
        return variables.get(key);
    }

    /**
     * Return the variable with the given name
     *
     * @param key variable name
     * @return content of the variable
     */
    @Nullable
    <T> ContextVariable<T> get(String key, Class<T> clazz) {
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

    /**
     * Return whether the variable with the given name is {@code null} or empty.
     *
     * @param key the key for the variable
     * @return {@code true} if the variable is {@code null} or empty, {@code false} otherwise
     */
    public boolean isNullOrEmpty(String key) {
        return get(key) == null || get(key).isEmpty();
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
    @Nullable
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

    /**
     * Builder for ContextVariables
     */
    public static class Builder implements SemanticKernelBuilder<KernelFunctionArguments> {

        private final Map<String, ContextVariable<?>> variables;

        /**
         * Create a new instance of Builder.
         */
        public Builder() {
            variables = new HashMap<>();
            this.variables.put(MAIN_KEY, ContextVariable.of(""));
        }

        /**
         * Builds an instance with the given content in the default main key
         *
         * @param content Entry to place in the "input" slot
         * @param <T>     Type of the value
         * @return {$code this} Builder for fluent coding
         */
        public <T> Builder withInput(ContextVariable<T> content) {
            return withVariable(MAIN_KEY, content);
        }

        /**
         * Builds an instance with the given content in the default main key
         *
         * @param content Entry to place in the "input" slot
         * @return {$code this} Builder for fluent coding
         * @throws SKException if the content cannot be converted to a ContextVariable
         */
        public Builder withInput(Object content) {
            return withInput(ContextVariable.ofGlobalType(content));
        }

        /**
         * Builds an instance with the given content in the default main key
         *
         * @param content       Entry to place in the "input" slot
         * @param typeConverter Type converter for the content
         * @param <T>           Type of the value
         * @return {$code this} Builder for fluent coding
         * @throws SKException if the content cannot be converted to a ContextVariable
         */
        public <T> Builder withInput(T content, ContextVariableTypeConverter<T> typeConverter) {
            return withInput(new ContextVariable<>(
                new ContextVariableType<>(
                    typeConverter,
                    typeConverter.getType()),
                content));
        }

        /**
         * Builds an instance with the given variables
         *
         * @param map Existing variables
         * @return {$code this} Builder for fluent coding
         */
        public Builder withVariables(@Nullable Map<String, ContextVariable<?>> map) {
            if (map == null) {
                return this;
            }
            variables.putAll(map);
            return this;
        }

        /**
         * Set variable
         *
         * @param key   variable name
         * @param value variable value
         * @param <T>   Type of the value
         * @return {$code this} Builder for fluent coding
         */
        public <T> Builder withVariable(String key, ContextVariable<T> value) {
            variables.put(key, value);
            return this;
        }

        /**
         * Set variable, uses the default type converters
         *
         * @param key   variable name
         * @param value variable value
         * @return {$code this} Builder for fluent coding
         * @throws SKException if the value cannot be converted to a ContextVariable
         */
        public Builder withVariable(String key, Object value) {
            return withVariable(key, ContextVariable.ofGlobalType(value));
        }

        /**
         * Set variable
         *
         * @param key           variable name
         * @param value         variable value
         * @param typeConverter Type converter for the value
         * @param <T>           Type of the value
         * @return {$code this} Builder for fluent coding
         * @throws SKException if the value cannot be converted to a ContextVariable
         */
        public <T> Builder withVariable(String key, T value,
            ContextVariableTypeConverter<T> typeConverter) {
            return withVariable(key, new ContextVariable<>(
                new ContextVariableType<>(
                    typeConverter,
                    typeConverter.getType()),
                value));
        }

        @Override
        public KernelFunctionArguments build() {
            return new KernelFunctionArguments(variables);
        }
    }
}
