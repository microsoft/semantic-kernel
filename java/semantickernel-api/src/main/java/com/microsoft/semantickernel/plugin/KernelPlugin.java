package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import java.util.Collections;
import java.util.Iterator;
import java.util.Map;

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
            this.functions.putAll(plugins);
        }
    }

    public Map<String, KernelFunction> getFunctions() {
        return Collections.unmodifiableMap(functions);
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
