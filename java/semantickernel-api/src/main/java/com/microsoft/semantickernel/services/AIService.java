// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.util.Map;
import javax.annotation.Nullable;

/**
 * Marker interface for AI services. {@code AIService}s are registered with the {@code Kernel} 
 * and are used to provide access to AI services.
 */
public interface AIService {

    /**
     * Gets the attributes of the service.
     * @return The attributes of the service.
     */
    Map<String, ContextVariable<?>> getAttributes();

    /**
     * Key used to store the model identifier in the {@code attributes} map.
     */
    String MODEL_ID_KEY = "ModelId";

    /**
     * Key used to store the endpoint in the {@code attributes} map.
     */
    String ENDPOINT_KEY = "Endpoint";

    /**
     * Key used to store the API version in the {@code attributes} map.
     */

    String API_VERSION_KEY = "ApiVersion";

    /**
     * Gets the model identifier from the {@code attributes} map.
     *
     * @return The model identifier if it was specified in the service's attributes; otherwise,
     * {@code null}.
     */
    @Nullable
    default String getModelId() {
        return getAttribute(this, MODEL_ID_KEY);
    }

    /**
     * Gets the endpoint from the {@code attributes} map.
     *
     * @return The endpoint if it was specified in the service's attributes; otherwise, {@code null}.
     */
    @Nullable
    default String getEndpoint() {
        return getAttribute(this, ENDPOINT_KEY);
    }

    /**
     * Gets the API version from the {@code attributes} map.
     *
     * @return The API version if it was specified in the service's attributes; otherwise, {@code null}.
     */
    @Nullable
    default String getApiVersion() {
        return getAttribute(this, API_VERSION_KEY);
    }

    /**
     * Gets the service identifier.
     * @return The service identifier.
     */
    @Nullable
    String getServiceId();

    /**
     * Get the named attribute from the service's attributes.
     * @param service The service to get the attribute from.
     * @param key The key of the attribute to get.
     * @return The value of the attribute if it exists; otherwise, {@code null}.
     */
    @Nullable
    static String getAttribute(AIService service, String key) {
        if (service.getAttributes() != null) {
            ContextVariable<?> contextVariable = service.getAttributes().get(key);
            if (contextVariable != null) {
                return contextVariable.getValue(String.class);
            }
        }
        return null;
    }
}
