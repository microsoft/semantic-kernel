// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import javax.annotation.Nullable;

/**
 * Represents a selector which will return an {@link AIServiceSelection} containing instances of
 * {@link AIService} and {@link com.microsoft.semantickernel.orchestration.PromptExecutionSettings}
 * from the specified provider based on the model settings.
 */
public interface AIServiceSelector {

    /**
     * Resolves an {@link AIService} and associated and
     * {@link com.microsoft.semantickernel.orchestration.PromptExecutionSettings} based on the 
     * associated {@link KernelFunction} and {@link KernelFunctionArguments}.
     *
     * @param serviceType The type of service to select.  This must be the same type with which the
     *                    service was registered in the {@link AIServiceSelection}
     * @param function The KernelFunction to use to select the service, or {@code null}.
     * @param arguments The KernelFunctionArguments to use to select the service, or {@code null}.
     * @param <T> The type of service to select.
     * @return An {@code AIServiceSelection} containing the selected service and associated PromptExecutionSettings.
     */
    @Nullable
    <T extends AIService> AIServiceSelection<T> trySelectAIService(
        Class<T> serviceType,
        @Nullable KernelFunction<?> function,
        @Nullable KernelFunctionArguments arguments);
}
