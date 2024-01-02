// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

public class Plugin {

    private final String name;
    private final List<KernelFunction> functions;

    public Plugin(String name, KernelFunction... functions) {
        this.name = name;
        this.functions = functions != null ? Collections.unmodifiableList(Arrays.asList(functions))
            : Collections.emptyList();
    }

    public Plugin(String name, List<KernelFunction> functions) {
        this(name,
            functions != null ? functions.toArray(new KernelFunction[0]) : new KernelFunction[0]);
    }

    public String name() {
        return name;
    }

    public List<KernelFunction> functions() {
        return functions;
    }
}
