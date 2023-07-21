// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import com.microsoft.semantickernel.exceptions.ConfigurationException;

public abstract class OpenAIClientSettings {

    public static final String KEY_SUFFIX = "key";

    /**
     * Check if the settings are valid
     *
     * @return true if the settings are valid
     */
    public abstract boolean assertIsValid() throws ConfigurationException;

    /**
     * Get the Azure OpenAI key
     *
     * @return Azure OpenAI key
     */
    public abstract String getKey();
}
