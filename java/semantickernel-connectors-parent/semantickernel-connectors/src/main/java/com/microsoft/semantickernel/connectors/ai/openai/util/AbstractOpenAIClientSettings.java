// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import com.microsoft.semantickernel.exceptions.ConfigurationException;

/**
 * Settings for an OpenAI client that uses a specific OpenAI provider such as openai.com or Azure
 * OpenAI.
 */
public abstract class AbstractOpenAIClientSettings {

    public static final String KEY_SUFFIX = "key";

    /**
     * Check if the settings are valid
     *
     * @return true if the settings are valid
     */
    public abstract boolean assertIsValid() throws ConfigurationException;

    /**
     * Get the OpenAI client key
     *
     * @return OpenAI client key
     */
    public abstract String getKey();
}
