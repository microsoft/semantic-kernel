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
        Map<String, KernelFunction> plugins) {
        this.name = name;
        this.description = description;
        this.functions = new CaseInsensitiveMap<>();
        if (plugins != null) {
            plugins.forEach((key,kerneFunction) -> this.functions.put(key, kerneFunction));
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
