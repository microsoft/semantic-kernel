// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.util;

import java.io.IOException;

public class AzureOpenAISettings extends ClientSettings<AzureOpenAISettings> {

    private static final String DEFAULT_CLIENT_ID = "azureopenai";
    private String key;
    private String endpoint;
    private String deploymentName;

    public enum Property {
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

    public String getKey() {
        return key;
    }

    public String getEndpoint() {
        return endpoint;
    }

    public String getDeploymentName() {
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
}
