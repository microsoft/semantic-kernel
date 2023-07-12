// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

public abstract class ClientSettings<T extends ClientSettings<T>> {
    /**
     * Returns settings obtained from the environment
     *
     * @return T settings
     */
    public abstract T fromEnv();

    /**
     * Returns an instance of the settings defined by the properties fil
     *
     * @param path Path to the properties file
     * @return T settings
     * @throws IOException if the file cannot be read
     */
    public abstract T fromFile(String path) throws IOException;

    /**
     * Returns an instance of the settings defined by the properties fil
     *
     * @param path Path to the properties file
     * @param clientSettingsId ID of the client settings in the properties file schema
     * @return T settings
     * @throws IOException if the file cannot be read
     */
    public abstract T fromFile(String path, String clientSettingsId) throws IOException;

    /**
     * Check if the settings are valid
     *
     * @return true if the settings are valid
     */
    public abstract boolean isValid();

    /**
     * Returns an instance of the settings defined by the system properties
     *
     * @return T settings
     */
    public abstract T fromSystemProperties();

    /**
     * Returns an instance of the settings defined by the system properties
     *
     * @return T settings
     */
    public abstract T fromSystemProperties(String clientSettingsId);

    private static String getPropertyNameForClientId(String clientSettingsId, String propertyName) {
        return "client." + clientSettingsId + "." + propertyName;
    }

    /**
     * Returns the value of the property from the environment
     *
     * @param property Name of the property to retrieve
     * @return String value of the property
     */
    protected String getSettingsValueFromEnv(String property) {
        return System.getenv(property);
    }

    /**
     * Returns the value of the property from the properties file
     *
     * @param settingsFile Path to the properties file
     * @param property Name of the property to retrieve
     * @param clientSettingsId ID of the client settings in the properties file schema
     * @return String value of the property
     */
    protected String getSettingsValueFromFile(
            String settingsFile, String property, String clientSettingsId) throws IOException {
        File Settings = new File(settingsFile);

        try (FileInputStream fis = new FileInputStream(Settings.getAbsolutePath())) {
            Properties props = new Properties();
            props.load(fis);

            return props.getProperty(getPropertyNameForClientId(clientSettingsId, property));
        } catch (IOException e) {
            throw new IOException(settingsFile + " not configured properly");
        }
    }

    /**
     * Returns the value of the property from the system properties
     *
     * @param property Name of the property to retrieve
     * @param clientSettingsId ID of the client settings in the properties file
     * @return String value of the property
     */
    protected String getSettingsValueFromSystemProperties(
            String property, String clientSettingsId) {
        Properties props = System.getProperties();
        return props.getProperty(getPropertyNameForClientId(clientSettingsId, property));
    }
}
