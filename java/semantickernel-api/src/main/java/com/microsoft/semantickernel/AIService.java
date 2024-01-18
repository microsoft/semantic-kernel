// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.util.Map;

/**
 * Marker interface for AI services 
 */
public interface AIService {

    Map<String, ContextVariable<?>> getAttributes();
    
    /**
     * Key used to store the model identifier in the {@code attributes} map.
     */ 
    static final String MODEL_ID_KEY = "ModelId";

    /**
     * Key used to store the endpoint in the {@code attributes} map.
     */ 
    static final String ENDPOINT_KEY = "Endpoint";

    /**
     * Key used to store the API version in the {@code attributes} map.
     */ 

    static final String API_VERSION_KEY = "ApiVersion";

    /** 
     * Gets the model identifier from the {@code attributes} map.
     * @return The model identifier if it was specified in the service's attributes; otherwise, null.
     */
    default String getModelId() { return getAttribute(this, MODEL_ID_KEY); }

    /**
     * Gets the endpoint from the {@code attributes} map.
     * @return The endpoint if it was specified in the service's attributes; otherwise, null.
     */
    default String getEndpoint() { return getAttribute(this, ENDPOINT_KEY); }

    /**
     * Gets the API version from the {@code attributes} map.
     * @return The API version if it was specified in the service's attributes; otherwise, null.
     */
    default String getApiVersion() { return getAttribute(this, API_VERSION_KEY); }

    String getServiceId();

    /// <summary>
    /// Gets the specified attribute.
    /// </summary>
    static String getAttribute(AIService service, String key)
    {
        if (service.getAttributes() != null) {
            ContextVariable<?> contextVariable = service.getAttributes().get(key);
            if (contextVariable != null) {
                return contextVariable.getValue().toString();
            }
        }
        return null;
    }
}
