package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import java.util.Map;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class BaseAIServiceSelector implements AIServiceSelector {

    private static final Logger LOGGER = LoggerFactory.getLogger(BaseAIServiceSelector.class);

    protected final Map<Class<? extends AIService>, AIService> services;

    protected BaseAIServiceSelector(Map<Class<? extends AIService>, AIService> services) {
        this.services = services;
    }

    @Override
    @Nullable
    public <T extends AIService> AIServiceSelection<T> trySelectAIService(
        Class<T> serviceType,
        @Nullable
        KernelFunction function,

        @Nullable
        KernelArguments arguments
    ) {
        return trySelectAIService(serviceType, function, arguments, services);
    }

    @Nullable
    public abstract <T extends AIService> AIServiceSelection<T> trySelectAIService(
        Class<T> serviceType,

        @Nullable
        KernelFunction function,

        @Nullable
        KernelArguments arguments,
        Map<Class<? extends AIService>, AIService> services);
}
