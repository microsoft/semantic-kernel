// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import javax.annotation.Nullable;

/**
 * The result of an AI service selection.
 * @param <T> The type of AI service.
 */
public class AIServiceSelection<T extends AIService> {

    private final T service;
    @Nullable
    private final PromptExecutionSettings settings;

    /**
     * Creates a new AI service selection.
     *
     * @param service  The selected AI service.
     * @param settings The settings associated with the selected service. This may be {@code null} even if a
     *                 service is selected..
     */
    public AIServiceSelection(T service, @Nullable PromptExecutionSettings settings) {
        this.service = service;
        this.settings = settings;
    }

    /**
     * Gets the selected AI service.
     *
     * @return The selected AI service.
     */
    public T getService() {
        return service;
    }

    /**
     * Gets the settings associated with the selected service.
     *
     * @return The settings associated with the selected service. This may be {@code null} even if a service
     * is selected.
     */
    @Nullable
    public PromptExecutionSettings getSettings() {
        return settings;
    }
}
