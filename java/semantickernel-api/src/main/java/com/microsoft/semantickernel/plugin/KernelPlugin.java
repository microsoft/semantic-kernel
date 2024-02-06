package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import java.util.Collections;
import java.util.Iterator;
import java.util.Map;
import javax.annotation.Nullable;

public class KernelPlugin implements Iterable<KernelFunction<?>> {

    private final String name;
    @Nullable
    private final String description;

    private final CaseInsensitiveMap<KernelFunction<?>> functions;

    public KernelPlugin(
        String name,
        @Nullable
        String description,
        Map<String, KernelFunction<?>> plugins) {
        this.name = name;
        this.description = description;
        this.functions = new CaseInsensitiveMap<>();
        if (plugins != null) {
            this.functions.putAll(plugins);
        }
    }

    public void addFunction(KernelFunction<?> function) {
        functions.put(function.getName(), function);
    }

    public Map<String, KernelFunction<?>> getFunctions() {
        return Collections.unmodifiableMap(functions);
    }

    @Nullable
    @SuppressWarnings("unchecked")
    public <T> KernelFunction<T> get(String functionName) {
        return (KernelFunction<T>) functions.get(functionName);
    }

    @Override
    public Iterator<KernelFunction<?>> iterator() {
        return functions.values().iterator();
    }

    public String getName() {
        return name;
    }

    @Nullable
    public String getDescription() {
        return description;
    }
}
