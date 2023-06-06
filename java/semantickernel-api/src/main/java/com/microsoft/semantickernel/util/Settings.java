// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

public class Settings {
    private static final Logger LOGGER = LoggerFactory.getLogger(Settings.class);

    public static class OpenAISettings {
        private final String key;
        private final String organizationId;

        OpenAISettings(String key, String organizationId) {
            this.key = key;
            this.organizationId = organizationId;
        }

        public String getKey() {
            return key;
        }

        public String getOrganizationId() {
            return organizationId;
        }
    }

    public static class AzureOpenAISettings {
        private final String key;
        private final String endpoint;
        private final String deploymentName;

        public AzureOpenAISettings(String key, String endpoint, String deploymentName) {
            this.key = key;
            this.endpoint = endpoint;
            this.deploymentName = deploymentName;
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
    }

    private enum Property {
        OPEN_AI_KEY("openai.key"),
        OPEN_AI_ORGANIZATION_ID("openai.organizationid"),
        AZURE_OPEN_AI_KEY("azureopenai.key"),
        AZURE_OPEN_AI_ENDPOINT("azureopenai.endpoint"),
        AZURE_OPEN_AI_DEPLOYMENT_NAME("azureopenai.deploymentname");

        public final String label;

        Property(String label) {
            this.label = label;
        }
    }

    /**
     * Returns an instance of OpenAISettings with key and organizationId from the properties file
     *
     * @param path Path to the properties file
     * @return OpenAISettings
     */
    public static OpenAISettings getOpenAISettingsFromFile(String path) throws IOException {
        return new OpenAISettings(
                Settings.getSettingsValue(path, Property.OPEN_AI_KEY.label),
                Settings.getSettingsValue(path, Property.OPEN_AI_ORGANIZATION_ID.label, ""));
    }

    /**
     * Returns an instance of AzureOpenAISettings with key, endpoint and deploymentName from the
     * properties file
     *
     * @param path Path to the properties file
     * @return OpenAISettings
     */
    public static AzureOpenAISettings getAzureOpenAISettingsFromFile(String path)
            throws IOException {
        return new AzureOpenAISettings(
                Settings.getSettingsValue(path, Property.AZURE_OPEN_AI_KEY.label),
                Settings.getSettingsValue(path, Property.AZURE_OPEN_AI_ENDPOINT.label),
                Settings.getSettingsValue(path, Property.AZURE_OPEN_AI_DEPLOYMENT_NAME.label, ""));
    }

    private static String getSettingsValue(String settingsFile, String propertyName)
            throws IOException {
        return getSettingsValue(settingsFile, propertyName, null);
    }

    private static String getSettingsValue(
            String settingsFile, String propertyName, String defaultValue) throws IOException {
        File Settings = new File(settingsFile);
        try (FileInputStream fis = new FileInputStream(Settings.getAbsolutePath())) {
            Properties props = new Properties();
            props.load(fis);
            if (defaultValue == null) {
                return props.getProperty(propertyName);
            }
            return props.getProperty(propertyName, defaultValue);
        } catch (IOException e) {
            LOGGER.error(
                    "Unable to load config value " + propertyName + " from properties file", e);
            throw new IOException(settingsFile + " not configured properly");
        }
    }
}
