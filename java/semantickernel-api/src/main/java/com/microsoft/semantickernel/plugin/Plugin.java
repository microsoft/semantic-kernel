// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * A plugin contains one or more {@link KernelFunction}s.
 */
public class Plugin {

    private final String name;
    private final List<KernelFunction<?>> functions;

    /**
     * Creates a new instance of {@link Plugin}.
     *
     * @param name the name of the plugin
     * @param functions the functions of the plugin
     */
    public Plugin(String name, KernelFunction<?>... functions) {
        this.name = name;
        this.functions = functions != null ? Collections.unmodifiableList(Arrays.asList(functions))
            : Collections.emptyList();
    }

    /**
     * Creates a new instance of {@link Plugin}.
     *
     * @param name the name of the plugin
     * @param functions the functions of the plugin
     */
    public Plugin(String name, List<KernelFunction<?>> functions) {
        this(name,
            functions != null ? functions.toArray(new KernelFunction[0]) : new KernelFunction[0]);
    }

    /**
     * Gets the name of the plugin.
     *
     * @return the name of the plugin
     */
    public String name() {
        return name;
    }

    /**
     * Gets the functions of the plugin.
     *
     * @return the functions of the plugin
     */
    public List<KernelFunction<?>> functions() {
        return Collections.unmodifiableList(functions);
    }
}
