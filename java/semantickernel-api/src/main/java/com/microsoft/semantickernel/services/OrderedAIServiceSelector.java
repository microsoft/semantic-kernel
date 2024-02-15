package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.implementation.Verify;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Implementation of {@link com.microsoft.semantickernel.services.AIServiceSelector} that 
 * selects the AI service based on the order of the execution settings.
 * Uses the service id or model id to select the preferred service provider and then 
 * returns the service and associated execution settings.
 */
public class OrderedAIServiceSelector extends BaseAIServiceSelector {

    private static final Logger LOGGER = LoggerFactory.getLogger(OrderedAIServiceSelector.class);

    /**
     * Initializes a new instance of the {@link OrderedAIServiceSelector} 
     * class with an empty collection of services.
     */
    public OrderedAIServiceSelector() {
        super(new AiServiceCollection());
    }

    /**
     * Initializes a new instance of the {@link OrderedAIServiceSelector} 
     * class with the specified services.
     *
     * @param services The services to select from.
     */
    public OrderedAIServiceSelector(AiServiceCollection services) {
        super(services);
    }

    @Nullable
    @Override
    public <T extends AIService> AIServiceSelection<T> trySelectAIService(
        Class<T> serviceType,
        @Nullable KernelFunction<?> function,
        @Nullable KernelFunctionArguments arguments,
        Map<Class<? extends AIService>, AIService> services) {

        // Allow the execution settings from the kernel arguments to take precedence
        Map<String, PromptExecutionSettings> executionSettings = settingsFromFunctionSettings(
            function);

        if (executionSettings == null || executionSettings.isEmpty()) {
            AIService service = getAnyService(serviceType);
            if (service != null) {
                return castServiceSelection(new AIServiceSelection<>(service, null));
            }
        } else {
            AIServiceSelection<?> selection = executionSettings
                .entrySet()
                .stream()
                .map(keyValue -> {

                    PromptExecutionSettings settings = keyValue.getValue();
                    String serviceId = keyValue.getKey();

                    if (!Verify.isNullOrEmpty(serviceId)) {
                        AIService service = getService(serviceId);
                        if (service != null) {
                            return castServiceSelection(
                                new AIServiceSelection<>(service, settings));
                        }
                    }

                    return null;
                })
                .filter(Objects::nonNull)
                .findFirst()
                .orElseGet(() -> null);

            if (selection != null) {
                return castServiceSelection(selection);
            }

            selection = executionSettings
                .entrySet()
                .stream()
                .map(keyValue -> {
                    PromptExecutionSettings settings = keyValue.getValue();

                    if (!Verify.isNullOrEmpty(settings.getModelId())) {
                        AIService service = getServiceByModelId(settings.getModelId());
                        if (service != null) {
                            return castServiceSelection(
                                new AIServiceSelection<>(service, settings));
                        }
                    }

                    return null;
                })
                .filter(Objects::nonNull)
                .findFirst()
                .orElseGet(() -> null);

            if (selection != null) {
                return castServiceSelection(selection);
            }
        }

        AIService defaultService = getService(PromptExecutionSettings.DEFAULT_SERVICE_ID);

        if (defaultService != null && serviceType.isAssignableFrom(defaultService.getClass())) {
            return castServiceSelection(new AIServiceSelection<>(defaultService, null));
        }

        AIService service = getAnyService(serviceType);
        PromptExecutionSettings settings = null;

        if (executionSettings != null && !executionSettings.isEmpty()) {
            if (executionSettings.containsKey(PromptExecutionSettings.DEFAULT_SERVICE_ID)) {
                settings = executionSettings.get(PromptExecutionSettings.DEFAULT_SERVICE_ID);
            } else {
                settings = executionSettings.values().stream().findFirst().orElseGet(() -> null);
            }
        }

        if (service != null) {
            return castServiceSelection(new AIServiceSelection<>(service, settings));
        }

        LOGGER.warn("No service found meeting requirements");
        return null;
    }

    @SuppressWarnings("unchecked")
    @Nullable
    private static <T extends AIService> AIServiceSelection<T> castServiceSelection(
        AIServiceSelection<?> selection) {
        try {
            // unchecked cast
            return (AIServiceSelection<T>) selection;
        } catch (ClassCastException e) {
            LOGGER.debug("%s", e.getMessage());
            return null;
        }
    }

    @Nullable
    private static Map<String, PromptExecutionSettings> settingsFromFunctionSettings(
        @Nullable KernelFunction function) {
        if (function != null) {
            return function.getExecutionSettings();
        }
        return null;
    }

    private AIService getServiceByModelId(String modelId) {
        return services
            .values()
            .stream()
            .filter(s -> modelId.equalsIgnoreCase(s.getModelId()))
            .findFirst()
            .orElseGet(() -> null);
    }

    /**
     * Gets the service with the specified service id.
     *
     * @param serviceId The service id.
     * @return The service with the specified service id, or {@code null} if no such service exists.
     * @see AIService#getServiceId()
     */
    @Nullable
    public AIService getService(String serviceId) {
        return services
            .values()
            .stream()
            .filter(s -> serviceId.equalsIgnoreCase(s.getServiceId()))
            .findFirst()
            .orElseGet(() -> null);
    }

    /**
     * Gets the service of the specified type.
     *
     * @param clazz The type of service to get.
     * @param <T> The type of service to get.
     * @return The service of the specified type, or {@code null} if no such service exists.
     */
    @Nullable
    @SuppressWarnings("unchecked")
    public <T extends AIService> T getService(Class<T> clazz) {
        T service = (T) services.get(clazz);

        if (service == null) {
            service = (T) services
                .entrySet()
                .stream()
                .filter(it -> clazz.isAssignableFrom(it.getKey()))
                .map(it -> it.getValue())
                .findFirst()
                .orElseGet(() -> null);
        }

        if (service == null &&
            (clazz.equals(TextGenerationService.class) ||
                clazz.equals(ChatCompletionService.class))) {
            LOGGER.warn(
                "Requested a non-existent service type of {}. Consider requesting a TextAIService instead.",
                clazz.getName());
        }

        return service;
    }

    /**
     * Gets the first service of the specified type, or that is an instance of the specified type.
     *
     * @param serviceType The type of service to get.
     * @return The first service of the specified type, or {@code null} if no such service exists.
     */
    @Nullable
    AIService getAnyService(Class<? extends AIService> serviceType) {
        List<AIService> matchingServices = getServices(serviceType);
        if (matchingServices.isEmpty()) {
            return null;
        }
        return matchingServices.get(0);
    }

    private List<AIService> getServices(Class<? extends AIService> serviceType) {
        return services
            .entrySet()
            .stream()
            .filter(it -> serviceType.isAssignableFrom(it.getKey()))
            .map(Map.Entry::getValue)
            .collect(Collectors.toList());
    }

}
