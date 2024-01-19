package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import java.util.HashMap;
import java.util.Map;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class ParentAIServiceSelector implements AIServiceSelector {

    private static final Logger LOGGER = LoggerFactory.getLogger(ParentAIServiceSelector.class);

    protected final Map<Class<? extends AIService>, AIService> services;

    public ParentAIServiceSelector() {
        this.services = new HashMap<>();
    }

    public ParentAIServiceSelector(Map<Class<? extends AIService>, AIService> services) {
        this.services = services;
    }

    @Override
    @Nullable
    public AIServiceSelection trySelectAIService(
        Class<? extends AIService> serviceType,
        KernelFunction function,
        KernelArguments arguments) {
        return trySelectAIService(serviceType, function, arguments, services);
    }

    @Nullable
    public abstract AIServiceSelection trySelectAIService(
        Class<? extends AIService> serviceType,
        KernelFunction function,
        KernelArguments arguments,
        Map<Class<? extends AIService>, AIService> services);
}
