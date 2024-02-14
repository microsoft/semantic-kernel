package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import java.util.Map;

import javax.annotation.Nullable;

/**
 * Base class for {@link AIServiceSelector} implementations which provides a 
 * {@code Map} based collection from which an {@link AIService} can be selected.
 * The {@link #trySelectAIService(Class, KernelFunction, KernelFunctionArguments)}
 * method has been implemented. Child classes must implement the method
 * {@link #trySelectAIService(Class, KernelFunction, KernelFunctionArguments, Map)}.
 */
public abstract class BaseAIServiceSelector implements AIServiceSelector {

    protected final Map<Class<? extends AIService>, AIService> services;

    /**
     * Initializes a new instance of the {@link BaseAIServiceSelector} class.
     *
     * @param services The services to select from.
     */
    protected BaseAIServiceSelector(Map<Class<? extends AIService>, AIService> services) {
        this.services = services;
    }

    @Override
    @Nullable
    public <T extends AIService> AIServiceSelection<T> trySelectAIService(
        Class<T> serviceType,
        @Nullable KernelFunction<?> function,
        @Nullable KernelFunctionArguments arguments) {
        return trySelectAIService(serviceType, function, arguments, services);
    }

    /**
     * Resolves an {@link AIService} from the {@code services} argument using
     * the specified {@code function} and {@code arguments} for selection.
     *
     * @param serviceType The type of service to select.  This must be the same type with which the
     *                    service was registered in the {@link AIServiceSelection}
     * @param function The KernelFunction to use to select the service, or {@code null}.
     * @param arguments The KernelFunctionArguments to use to select the service, or {@code null}.
     * @param services The services to select from.
     * @param <T> The type of service to select.
     * @return
     */
    @Nullable
    protected abstract <T extends AIService> AIServiceSelection<T> trySelectAIService(
        Class<T> serviceType,
        @Nullable KernelFunction<?> function,
        @Nullable KernelFunctionArguments arguments,
        Map<Class<? extends AIService>, AIService> services);
}
