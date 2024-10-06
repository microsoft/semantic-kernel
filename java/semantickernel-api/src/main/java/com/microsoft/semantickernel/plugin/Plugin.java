// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugin;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import com.microsoft.semantickernel.orchestration.SKFunction;

public class Plugin {
    
    private final String name;
    private final List<SKFunction> functions;

    public Plugin(String name, SKFunction... functions) {
        this.name = name;
        this.functions = functions != null ? Collections.unmodifiableList(Arrays.asList(functions)) : Collections.emptyList();
    }

    public Plugin(String name, List<SKFunction> functions) {
        this(name, functions != null ? functions.toArray(new SKFunction[0]) : new SKFunction[0]);
    }

    public String name() { return name; }

    public List<SKFunction> functions() { return functions; }
}
