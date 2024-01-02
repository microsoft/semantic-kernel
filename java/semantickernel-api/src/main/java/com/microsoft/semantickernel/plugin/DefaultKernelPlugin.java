package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import java.util.Map;

public class DefaultKernelPlugin extends KernelPlugin {

    /// <summary>The collection of functions associated with this plugin.</summary>
    private final Map<String, KernelFunction> functions;

    public DefaultKernelPlugin(String name, String description,
        Map<String, KernelFunction> functions) {
        super(name, description);

        this.functions = new CaseInsensitiveMap<>(functions);
    }

    public Map<String, KernelFunction> getFunctions() {
        return functions;
    }

    @Override
    public KernelFunction get(String functionName) {
        return functions.get(functionName);
    }
}
