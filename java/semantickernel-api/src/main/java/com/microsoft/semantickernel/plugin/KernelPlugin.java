package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

public abstract class KernelPlugin implements Iterable<KernelFunction> {

    private final String name;
    private final String description;

    protected KernelPlugin(String name, String description) {
        this.name = name;
        this.description = description;
    }

    public abstract Iterator<KernelFunction> iterator();

    public abstract Map<String, KernelFunction> getFunctions();

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public abstract KernelFunction get(String functionName);

}
