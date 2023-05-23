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

    public enum Property {
        OPEN_AI_KEY("openai.key"),
        OPEN_AI_ORGANIZATION_ID("openai.organizationid"),
        AZURE_OPEN_AI_KEY("azureopenai.key"),
        AZURE_OPEN_AI_ENDPOINT("azureopenai.endpoint"),
        AZURE_OPEN_AI_DEPLOYMENT_NAME("azureopenai.deploymentname");

        public final String fileLabel;

        Property(String fileLabel) {
            this.fileLabel = fileLabel;
        }
    }

    /**
     * Returns an instance of OpenAISettings with key and organizationId from the environment
     *
     * @return OpenAISettings
     */
    public static OpenAISettings getOpenAISettingsFromEnv() {
        return new OpenAISettings(
                Settings.getSettingsValueFromEnv(Property.OPEN_AI_KEY),
                Settings.getSettingsValueFromEnv(Property.OPEN_AI_ORGANIZATION_ID));
    }

    /**
     * Returns an instance of AzureOpenAISettings with key, endpoint and deploymentName from the
     * environment
     *
     * @return AzureOpenAISettings
     */
    public static AzureOpenAISettings getAzureOpenAISettingsFromEnv() {
        return new AzureOpenAISettings(
                Settings.getSettingsValueFromEnv(Property.AZURE_OPEN_AI_KEY),
                Settings.getSettingsValueFromEnv(Property.AZURE_OPEN_AI_ENDPOINT),
                Settings.getSettingsValueFromEnv(Property.AZURE_OPEN_AI_DEPLOYMENT_NAME));
    }

    /**
     * Returns an instance of OpenAISettings with key and organizationId from the properties file
     *
     * @param path Path to the properties file
     * @return OpenAISettings
     */
    public static OpenAISettings getOpenAISettingsFromFile(String path) throws IOException {
        return new OpenAISettings(
                Settings.getSettingsValueFromFile(path, Property.OPEN_AI_KEY),
                Settings.getSettingsValueFromFile(path, Property.OPEN_AI_ORGANIZATION_ID, ""));
    }

    /**
     * Returns an instance of AzureOpenAISettings with key, endpoint and deploymentName from the
     * properties file
     *
     * @param path Path to the properties file
     * @return AzureOpenAISettings
     */
    public static AzureOpenAISettings getAzureOpenAISettingsFromFile(String path)
            throws IOException {
        return new AzureOpenAISettings(
                Settings.getSettingsValueFromFile(path, Property.AZURE_OPEN_AI_KEY),
                Settings.getSettingsValueFromFile(path, Property.AZURE_OPEN_AI_ENDPOINT),
                Settings.getSettingsValueFromFile(
                        path, Property.AZURE_OPEN_AI_DEPLOYMENT_NAME, ""));
    }

    /**
     * Returns the value associated to the env var with the name of the Property
     *
     * @param property Property to get the env var value from
     * @return String
     */
    public static String getSettingsValueFromEnv(Property property) {
        return System.getenv(property.name());
    }

    /**
     * Returns the Property value in the settingsFile
     *
     * @param settingsFile Properties file
     * @param property Property to retrieve from file
     * @return String with the value
     * @throws IOException
     */
    public static String getSettingsValueFromFile(String settingsFile, Property property)
            throws IOException {
        return getSettingsValueFromFile(settingsFile, property, null);
    }

    /**
     * Returns the Property value in the settingsFile
     *
     * @param settingsFile Properties file
     * @param property Property to retrieve from file
     * @param defaultValue Default value of the Property
     * @return String with the value
     * @throws IOException
     */
    public static String getSettingsValueFromFile(
            String settingsFile, Property property, String defaultValue) throws IOException {
        File Settings = new File(settingsFile);
        try (FileInputStream fis = new FileInputStream(Settings.getAbsolutePath())) {
            Properties props = new Properties();
            props.load(fis);
            return props.getProperty(property.fileLabel, defaultValue);
        } catch (IOException e) {
            LOGGER.error(
                    "Unable to load config value " + property.fileLabel + " from properties file",
                    e);
            throw new IOException(settingsFile + " not configured properly");
        }
    }
}
