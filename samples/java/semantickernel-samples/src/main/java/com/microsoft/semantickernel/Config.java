package com.microsoft.semantickernel;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

public class Config {

    private static final Logger LOGGER = LoggerFactory.getLogger(Config.class);

    public static String getOpenAIKey(String conf) {
        return getConfigValue(conf, "token");
    }

    public static String getAzureOpenAIEndpoint(String conf) {
        return getConfigValue(conf, "endpoint");
    }

    private static String getConfigValue(String configFile, String propertyName) {
        File config = new File(configFile);
        try (FileInputStream fis = new FileInputStream(config.getAbsolutePath())) {
            Properties props = new Properties();
            props.load(fis);
            return props.getProperty(propertyName);
        } catch (IOException e) {
            LOGGER.error("Unable to load config value " + propertyName + " from file" + configFile, e);
            throw new RuntimeException(configFile + " not configured properly");
        }
    }
}
