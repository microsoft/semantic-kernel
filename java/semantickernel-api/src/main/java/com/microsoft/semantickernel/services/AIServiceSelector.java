// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import javax.annotation.Nullable;

/**
 * Represents a selector which will return an {@link AIServiceSelection} containing instances of
 * {@link AIService} and {@link com.microsoft.semantickernel.orchestration.PromptExecutionSettings}
 * from the specified provider based on the model settings.
 */
public interface AIServiceSelector {

    /**
     * Resolves an {@link AIService} and associated and
     * {@link com.microsoft.semantickernel.orchestration.PromptExecutionSettings} from the specified
     * {@link com.microsoft.semantickernel.Kernel} based on the associated {@link KernelFunction}
     * and {@link KernelArguments}.
     *
     * @param serviceType The type of service to select.  This must be the same type with which the
     *                    service was registered in the {@link AIServiceSelection}
     * @param function
     * @param arguments
     * @return
     */
    @Nullable
    AIServiceSelection trySelectAIService(
        Class<? extends AIService> serviceType,
        @Nullable
        KernelFunction function,

        @Nullable
        KernelArguments arguments
    );
}
