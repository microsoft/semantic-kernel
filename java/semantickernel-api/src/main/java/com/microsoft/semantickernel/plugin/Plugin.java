package com.microsoft.semantickernel.plugin;

import java.util.Collection;

import com.microsoft.semantickernel.orchestration.SKFunction;

public interface Plugin {
    String name();

    String description();

    Collection<SKFunction> functions();
}
