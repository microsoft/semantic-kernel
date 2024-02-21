// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import java.util.Collections;
import java.util.Iterator;
import java.util.Map;
import javax.annotation.Nullable;

/**
 * A plugin contains a collection of functions that can be invoked by the Semantic Kernel.
 */
public class KernelPlugin implements Iterable<KernelFunction<?>> {

    private final String name;
    @Nullable
    private final String description;

    private final CaseInsensitiveMap<KernelFunction<?>> functions;

    /**
     * Creates a new instance of the {@link KernelPlugin} class.
     *
     * @param name        The name of the plugin.
     * @param description The description of the plugin.
     * @param plugins     The functions in the plugin.
     */
    public KernelPlugin(
        String name,
        @Nullable String description,
        Map<String, KernelFunction<?>> plugins) {
        this.name = name;
        this.description = description;
        this.functions = new CaseInsensitiveMap<>();
        if (plugins != null) {
            this.functions.putAll(plugins);
        }
    }

    /**
     * Adds a function to the plugin.
     *
     * @param function The function to add.
     */
    public void addFunction(KernelFunction<?> function) {
        functions.put(function.getName(), function);
    }

    /**
     * Gets the functions in the plugin.
     *
     * @return The functions in the plugin.
     */
    public Map<String, KernelFunction<?>> getFunctions() {
        return Collections.unmodifiableMap(functions);
    }

    /**
     * Gets a function by name.
     *
     * @param functionName The name of the function.
     * @param <T>          The return type of the function.
     * @return The function with the specified name, or {@code null} if no such function exists.
     */
    @Nullable
    @SuppressWarnings("unchecked")
    public <T> KernelFunction<T> get(String functionName) {
        return (KernelFunction<T>) functions.get(functionName);
    }

    /**
     * Get an {@code Iterator} that iterates over the functions of this plugin.
     *
     * @return An {@code Iterator} that iterates over the functions of this plugin.
     */
    @Override
    public Iterator<KernelFunction<?>> iterator() {
        return functions.values().iterator();
    }

    /**
     * Gets the name of the plugin.
     *
     * @return The name of the plugin.
     */
    public String getName() {
        return name;
    }

    /**
     * Gets the description of the plugin.
     *
     * @return The description of the plugin.
     */
    @Nullable
    public String getDescription() {
        return description;
    }
}
