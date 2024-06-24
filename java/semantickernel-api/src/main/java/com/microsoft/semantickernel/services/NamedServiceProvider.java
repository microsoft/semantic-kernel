// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import javax.annotation.Nullable;

/**
 * A service provider for named services.
 *
 * @param <T> The type of the service.
 */
public interface NamedServiceProvider<T> {

    /**
     * Gets the service of the specified type and name, or {@code null} if not found.
     *
     * @param name  The name of the service, or {@code null} for the default service.
     * @param clazz The type of the service.
     * @param <U>   The specific type of the service
     * @return The service instance, or {@code null} if not found.
     */
    @Nullable
    public <U extends T> U getService(@Nullable String name, Class<U> clazz);
}
