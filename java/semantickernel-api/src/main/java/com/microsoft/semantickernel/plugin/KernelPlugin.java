package com.microsoft.semantickernel.plugin;

import java.util.Iterator;
import java.util.List;
import java.util.Map;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;

public class KernelPlugin implements Iterable<KernelFunction> {

    private final String name;
    private final String description;

    private final CaseInsensitiveMap<KernelFunction> functions;

    public KernelPlugin(String name, String description,
        List<KernelFunction> functions) {
        this.name = name;
        this.description = description;
        this.functions = new CaseInsensitiveMap<>();
        if (functions != null) {
            functions.forEach(x -> this.functions.put(x.getName(), x));
        }
    }

    public Map<String, KernelFunction> getFunctions() {
        return functions;
    }

    public KernelFunction get(String functionName) {
        return functions.get(functionName);
    }     

    @Override
    public Iterator<KernelFunction> iterator() {
        return functions.values().iterator();
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }
}
