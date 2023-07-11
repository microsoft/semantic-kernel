// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import java.io.IOException;

import javax.annotation.Nullable;

/** Settings for Azure OpenAI client */
public class AzureOpenAISettings extends ClientSettings<AzureOpenAISettings> {

    private static final String DEFAULT_CLIENT_ID = "azureopenai";

    @Nullable private String key = null;

    @Nullable private String endpoint = null;

    @Nullable private String deploymentName = null;

    private enum Property {
        AZURE_OPEN_AI_KEY("key"),
        AZURE_OPEN_AI_ENDPOINT("endpoint"),
        AZURE_OPEN_AI_DEPLOYMENT_NAME("deploymentname");
        private final String label;

        Property(String label) {
            this.label = label;
        }

        public String label() {
            return this.label;
        }
    }

    /**
     * Get the Azure OpenAI key
     *
     * @return Azure OpenAI key
     */
    public String getKey() {
        if (key == null) {
            throw new RuntimeException("Azure OpenAI key is not set");
        }
        return key;
    }

    /**
     * Get the Azure OpenAI endpoint
     *
     * @return Azure OpenAI endpoint
     */
    public String getEndpoint() {
        if (endpoint == null) {
            throw new RuntimeException("Azure OpenAI endpoint is not set");
        }
        return endpoint;
    }

    /**
     * Get the Azure OpenAI deployment name
     *
     * @return Azure OpenAI deployment name
     */
    public String getDeploymentName() {
        if (deploymentName == null) {
            throw new RuntimeException("Azure OpenAI deployment name is not set");
        }
        return deploymentName;
    }

    @Override
    public AzureOpenAISettings fromEnv() {
        this.key = getSettingsValueFromEnv(Property.AZURE_OPEN_AI_KEY.name());
        this.endpoint = getSettingsValueFromEnv(Property.AZURE_OPEN_AI_ENDPOINT.name());
        this.deploymentName =
                getSettingsValueFromEnv(Property.AZURE_OPEN_AI_DEPLOYMENT_NAME.name());
        return this;
    }

    @Override
    public AzureOpenAISettings fromFile(String path) throws IOException {
        return fromFile(path, DEFAULT_CLIENT_ID);
    }

    @Override
    public AzureOpenAISettings fromFile(String path, String clientSettingsId) throws IOException {
        this.key =
                getSettingsValueFromFile(
                        path, Property.AZURE_OPEN_AI_KEY.label(), clientSettingsId);
        this.endpoint =
                getSettingsValueFromFile(
                        path, Property.AZURE_OPEN_AI_ENDPOINT.label(), clientSettingsId);
        this.deploymentName =
                getSettingsValueFromFile(
                        path, Property.AZURE_OPEN_AI_DEPLOYMENT_NAME.label(), clientSettingsId);
        return this;
    }

    @Override
    public boolean isValid() {
        return key != null && endpoint != null;
    }

    @Override
    public AzureOpenAISettings fromSystemProperties() {
        return fromSystemProperties(DEFAULT_CLIENT_ID);
    }

    @Override
    public AzureOpenAISettings fromSystemProperties(String clientSettingsId) {
        this.key =
                getSettingsValueFromSystemProperties(
                        Property.AZURE_OPEN_AI_KEY.label(), clientSettingsId);
        this.endpoint =
                getSettingsValueFromSystemProperties(
                        Property.AZURE_OPEN_AI_ENDPOINT.label(), clientSettingsId);
        this.deploymentName =
                getSettingsValueFromSystemProperties(
                        Property.AZURE_OPEN_AI_DEPLOYMENT_NAME.label(), clientSettingsId);
        return this;
    }
}
