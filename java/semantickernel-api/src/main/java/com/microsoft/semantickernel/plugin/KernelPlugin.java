package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import java.util.Iterator;

public abstract class KernelPlugin implements Iterable<KernelFunction> {

    private final String name;
    private final String description;

    protected KernelPlugin(String name, String description) {
        this.name = name;
        this.description = description;
    }

    @Override
    public Iterator<KernelFunction> iterator() {
        return null;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public abstract KernelFunction get(String functionName);
}
