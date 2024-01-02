// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelArguments;
import com.microsoft.semantickernel.KernelFunction;
import com.microsoft.semantickernel.PromptExecutionSettings;

/**
 * Represents a selector which will return an {@link AIServiceSelection} containing instances
 * of {@link AIService} and {@link PromptExecutionSettings} from the specified provider based 
 * on the model settings.
 */
public interface AIServiceSelector {
    
    /**
     * Resolves an {@link IAIService} and associated and {@link PromptExecutionSettings} from 
     * the specified {@link com.microsoft.semantickernel.Kernel} based on the associated
     * {@link com.microsoft.semantickernel.KernelFunction} and {@link com.microsoft.semantickernel.KernelArguments}.
     * @param serviceType The type of service to select.  This must be the same type
     *        with which the service was registered in the {@link AIServiceSelectionf}
     * @param kernel
     * @param function
     * @param arguments
     * @return
     */
    AIServiceSelection trySelectAIService(
        Class<? extends AIService> serviceType,
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments
    );   
}
