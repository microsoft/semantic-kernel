// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

public class ClientSettings {
    private static final Logger LOGGER = LoggerFactory.getLogger(ClientSettings.class);

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

    private static final String DEFAULT_OPEN_AI_CLIENT_ID = "openai";
    private static final String DEFAULT_AZURE_OPEN_AI_CLIENT_ID = "azureopenai";

    public enum Property {
        OPEN_AI_KEY(".key"),
        OPEN_AI_ORGANIZATION_ID(".organizationid"),
        AZURE_OPEN_AI_KEY(".key"),
        AZURE_OPEN_AI_ENDPOINT(".endpoint"),
        AZURE_OPEN_AI_DEPLOYMENT_NAME(".deploymentname");

        public final String labelSuffix;

        Property(String labelSuffix) {
            this.labelSuffix = labelSuffix;
        }

        String getPropertyNameForClientId(String clientSettingsId) {
            return "client." + clientSettingsId + labelSuffix;
        }
    }

    /**
     * Returns an instance of OpenAISettings with key and organizationId from the environment
     *
     * @return OpenAISettings
     */
    public static OpenAISettings getOpenAISettingsFromEnv() {
        return new OpenAISettings(
                ClientSettings.getSettingsValueFromEnv(Property.OPEN_AI_KEY),
                ClientSettings.getSettingsValueFromEnv(Property.OPEN_AI_ORGANIZATION_ID));
    }

    /**
     * Returns an instance of AzureOpenAISettings with key, endpoint and deploymentName from the
     * environment
     *
     * @return AzureOpenAISettings
     */
    public static AzureOpenAISettings getAzureOpenAISettingsFromEnv() {
        return new AzureOpenAISettings(
                ClientSettings.getSettingsValueFromEnv(Property.AZURE_OPEN_AI_KEY),
                ClientSettings.getSettingsValueFromEnv(Property.AZURE_OPEN_AI_ENDPOINT),
                ClientSettings.getSettingsValueFromEnv(Property.AZURE_OPEN_AI_DEPLOYMENT_NAME));
    }

    /**
     * Returns an instance of OpenAISettings with key and organizationId from the properties file
     *
     * @param path Path to the properties file
     * @return OpenAISettings
     */
    public static OpenAISettings getOpenAISettingsFromFile(String path) throws IOException {
        return getOpenAISettingsFromFile(path, DEFAULT_OPEN_AI_CLIENT_ID);
    }

    /**
     * Returns an instance of OpenAISettings with key and organizationId from the properties file
     *
     * @param path Path to the properties file
     * @param clientSettingsId ID of the client settings in the properties file schema
     * @return OpenAISettings
     */
    public static OpenAISettings getOpenAISettingsFromFile(String path, String clientSettingsId)
            throws IOException {
        return new OpenAISettings(
                ClientSettings.getSettingsValueFromFile(path, Property.OPEN_AI_KEY, clientSettingsId),
                ClientSettings.getSettingsValueFromFile(
                        path, Property.OPEN_AI_ORGANIZATION_ID, clientSettingsId));
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
        return getAzureOpenAISettingsFromFile(path, DEFAULT_AZURE_OPEN_AI_CLIENT_ID);
    }

    /**
     * Returns an instance of AzureOpenAISettings with key, endpoint and deploymentName from the
     * properties file
     *
     * @param path Path to the properties file
     * @param clientSettingsId ID of the client settings in the properties file schema
     * @return AzureOpenAISettings
     */
    public static AzureOpenAISettings getAzureOpenAISettingsFromFile(
            String path, String clientSettingsId) throws IOException {
        return new AzureOpenAISettings(
                ClientSettings.getSettingsValueFromFile(
                        path, Property.AZURE_OPEN_AI_KEY, clientSettingsId),
                ClientSettings.getSettingsValueFromFile(
                        path, Property.AZURE_OPEN_AI_ENDPOINT, clientSettingsId),
                ClientSettings.getSettingsValueFromFile(
                        path, Property.AZURE_OPEN_AI_DEPLOYMENT_NAME, clientSettingsId));
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
     * @param clientSettingsId ID of the client settings in the properties file schema
     * @throws IOException
     */
    public static String getSettingsValueFromFile(
            String settingsFile, Property property, String clientSettingsId) throws IOException {
        File Settings = new File(settingsFile);

        try (FileInputStream fis = new FileInputStream(Settings.getAbsolutePath())) {
            Properties props = new Properties();
            props.load(fis);

            return props.getProperty(property.getPropertyNameForClientId(clientSettingsId));
        } catch (IOException e) {
            LOGGER.error(
                    "Unable to load config value "
                            + property.getPropertyNameForClientId(clientSettingsId)
                            + " from properties file",
                    e);
            throw new IOException(settingsFile + " not configured properly");
        }
    }
}
