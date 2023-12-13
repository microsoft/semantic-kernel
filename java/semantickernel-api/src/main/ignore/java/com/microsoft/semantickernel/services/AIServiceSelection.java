// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.PromptExecutionSettings;

/**
 * The result of an AI service selection.
 */
public class AIServiceSelection {

    private final AIService service;
    private final PromptExecutionSettings settings;

    /**
     * Creates a new AI service selection.
     * @param service The selected AI service.
     * @param settings The settings associated with the selected service. This may be null even if a service is selected..
     */
    public AIServiceSelection(AIService service, PromptExecutionSettings settings) {
        this.service = service;
        this.settings = settings;
    }

    /**
     * Gets the selected AI service.
     * @return The selected AI service.
     */
    public AIService getService() {
        return service;
    }

    /**
     * Gets the settings associated with the selected service.
     * @return The settings associated with the selected service. This may be null even if a service is selected.
     */
    public PromptExecutionSettings getSettings() {
        return settings;
    }
}
