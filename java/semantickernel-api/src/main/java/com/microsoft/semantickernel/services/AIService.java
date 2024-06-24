// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import javax.annotation.Nullable;

/**
 * Marker interface for AI services. {@code AIService}s are registered with the {@code Kernel} and
 * are used to provide access to AI services.
 */
public interface AIService {

    /**
     * Gets the model identifier.
     *
     * @return The model identifier if it was specified in the service's attributes; otherwise,
     * {@code null}.
     */
    @Nullable
    String getModelId();

    /**
     * Gets the service identifier.
     *
     * @return The service identifier.
     */
    @Nullable
    String getServiceId();
}
