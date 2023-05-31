package com.microsoft.semantickernel.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

public abstract class ClientSettings<T extends ClientSettings<T>> {
    public abstract T fromEnv();
    public abstract T fromFile(String path) throws IOException;
    public abstract T fromFile(String path, String clientSettingsId) throws IOException;
    private static String getPropertyNameForClientId(String clientSettingsId, String propertyName) {
        return "client." + clientSettingsId + "." + propertyName;
    }
    protected String getSettingsValueFromEnv(String property) {
        return System.getenv(property);
    }
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
}
