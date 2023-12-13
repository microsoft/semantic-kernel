// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import javax.annotation.Nullable;

/**
 * Provides access to services.
 */
public interface ServiceProvider {

    // TODO: IServiceProvider is a .NET API for DI. Do we need to support this?
    // And how does NamedServiceProvider interface fit in?

    /**
     * Gets the service of the specified type and name, or null if not found.
     *
     * @param <U> The specific type of the service
     * @param clazz The type of the service.
     * @return The service instance, or null if not found.
     */
    @Nullable
    public <U> U getService(Class<U> clazz);
}
