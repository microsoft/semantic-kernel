// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import com.microsoft.semantickernel.exceptions.ConfigurationException;

import java.util.Map;

import javax.annotation.Nullable;

/** Settings for Azure OpenAI client */
public class AzureOpenAISettings extends AbstractOpenAIClientSettings {
    private static final String DEFAULT_SETTINGS_PREFIX = "client.azureopenai";
    private static final String AZURE_OPEN_AI_ENDPOINT_SUFFIX = "endpoint";
    private static final String AZURE_OPEN_AI_DEPLOYMENT_NAME_SUFFIX = "deploymentname";

    @Nullable private final String key;

    @Nullable private final String endpoint;

    @Nullable private final String deploymentName;
    private final String settingsPrefix;

    public AzureOpenAISettings(Map<String, String> settings) {
        this(DEFAULT_SETTINGS_PREFIX, settings);
    }

    public AzureOpenAISettings(String settingsPrefix, Map<String, String> settings) {
        this.settingsPrefix = settingsPrefix;
        key = settings.get(settingsPrefix + "." + KEY_SUFFIX);
        endpoint = settings.get(settingsPrefix + "." + AZURE_OPEN_AI_ENDPOINT_SUFFIX);
        deploymentName = settings.get(settingsPrefix + "." + AZURE_OPEN_AI_DEPLOYMENT_NAME_SUFFIX);
    }

    /**
     * Get the Azure OpenAI endpoint
     *
     * @return Azure OpenAI endpoint
     */
    public String getEndpoint() throws ConfigurationException {
        if (endpoint == null) {
            throw new ConfigurationException(
                    ConfigurationException.ErrorCodes.ValueNotFound, AZURE_OPEN_AI_ENDPOINT_SUFFIX);
        }
        return endpoint;
    }

    /**
     * Get the Azure OpenAI deployment name
     *
     * @return Azure OpenAI deployment name
     */
    public String getDeploymentName() throws ConfigurationException {
        if (deploymentName == null) {
            throw new ConfigurationException(
                    ConfigurationException.ErrorCodes.ValueNotFound,
                    AZURE_OPEN_AI_DEPLOYMENT_NAME_SUFFIX);
        }
        return deploymentName;
    }

    public String getKey() throws ConfigurationException {
        if (key == null) {
            throw new ConfigurationException(
                    ConfigurationException.ErrorCodes.ValueNotFound, KEY_SUFFIX);
        }
        return key;
    }

    @Override
    public boolean assertIsValid() throws ConfigurationException {
        if (key == null) {
            throw new ConfigurationException(
                    ConfigurationException.ErrorCodes.ValueNotFound,
                    settingsPrefix + "." + KEY_SUFFIX);
        }
        if (endpoint == null) {
            throw new ConfigurationException(
                    ConfigurationException.ErrorCodes.ValueNotFound,
                    settingsPrefix + "." + AZURE_OPEN_AI_ENDPOINT_SUFFIX);
        }

        return true;
    }
}
