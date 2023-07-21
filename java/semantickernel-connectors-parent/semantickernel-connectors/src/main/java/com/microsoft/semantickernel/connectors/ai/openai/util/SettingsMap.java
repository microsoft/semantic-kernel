// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import static com.microsoft.semantickernel.exceptions.ConfigurationException.ErrorCodes.ConfigurationNotFound;
import static com.microsoft.semantickernel.exceptions.ConfigurationException.ErrorCodes.CouldNotReadConfiguration;
import static com.microsoft.semantickernel.exceptions.ConfigurationException.ErrorCodes.NoValidConfigurationsFound;

import com.microsoft.semantickernel.exceptions.ConfigurationException;

import org.slf4j.Logger;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import javax.annotation.Nullable;

/**
 * Creates a map of settings to be used in configuration, the settings are loaded from the following
 * sources in the order of precedence (lower number in this list overrides a higher number):
 *
 * <ul>
 *   <li>1. Environment variables.
 *   <li>2. System properties.
 *   <li>3. Properties file set via CONF_PROPERTIES environment variable.
 *   <li>4. Properties file: ./conf.properties (Not used if CONF_PROPERTIES was set).
 *   <li>5. Properties file: ~/.sk/conf.properties (Not used if CONF_PROPERTIES was set).
 * </ul>
 */
public class SettingsMap {
    private static final Logger LOGGER = org.slf4j.LoggerFactory.getLogger(SettingsMap.class);

    public static final String CONF_PROPERTIES_NAME = "CONF_PROPERTIES";
    public static final String CONF_PROPERTIES =
            getEnvOrProperty(CONF_PROPERTIES_NAME, "conf.properties");

    private static final List<File> DEFAULT_PROPERTIES_LOCATIONS =
            Arrays.asList(
                    new File(new File(System.getProperty("user.home"), ".sk"), "conf.properties"),
                    new File("conf.properties"));
    @Nullable private static final Map<String, String> DEFAULT_INST;

    static {
        // Create the default instance
        Map<String, String> DEFAULT_INST_TMP;
        try {
            DEFAULT_INST_TMP = get(DEFAULT_PROPERTIES_LOCATIONS);
        } catch (ConfigurationException e) {
            LOGGER.error("Failed to load settings", e);
            DEFAULT_INST_TMP = null;
        }
        DEFAULT_INST = DEFAULT_INST_TMP;
    }

    /**
     * Get settings, looks for settings in the default locations
     *
     * @return A map of settings
     */
    public static Map<String, String> getDefault() throws ConfigurationException {
        if (DEFAULT_INST == null) {
            throw new ConfigurationException(NoValidConfigurationsFound);
        }
        return Collections.unmodifiableMap(DEFAULT_INST);
    }

    /**
     * Get settings, looks for settings in the locations plus the additional locations provided
     *
     * @param propertyFileLocations additional locations to look for settings
     * @return A client instance
     */
    public static Map<String, String> get(List<File> propertyFileLocations)
            throws ConfigurationException {
        return Collections.unmodifiableMap(loadAllSettings(propertyFileLocations));
    }

    /**
     * Get settings, looks for settings in the default locations plus the additional locations
     * provided
     *
     * @param propertyFileLocations additional locations to look for settings
     * @return A client instance
     */
    public static Map<String, String> getWithAdditional(List<File> propertyFileLocations)
            throws ConfigurationException {
        ArrayList<File> locations = new ArrayList<>(DEFAULT_PROPERTIES_LOCATIONS);
        locations.addAll(propertyFileLocations);
        return get(locations);
    }

    private static Map<String, String> loadAllSettings(List<File> propertyFileLocations)
            throws ConfigurationException {
        Properties properties = new Properties();

        if (getEnvOrProperty(CONF_PROPERTIES_NAME, null) != null) {
            // User has explicitly set CONF_PROPERTIES, so ONLY use that and System properties
            if (Files.isRegularFile(new File(CONF_PROPERTIES).toPath())) {
                try (FileInputStream fis = new FileInputStream(CONF_PROPERTIES)) {
                    properties.load(fis);
                } catch (FileNotFoundException e) {
                    throw new ConfigurationException(ConfigurationNotFound, CONF_PROPERTIES);
                } catch (IOException e) {
                    throw new ConfigurationException(CouldNotReadConfiguration, CONF_PROPERTIES);
                }
            }
        } else {
            // Use default locations
            propertyFileLocations.forEach(
                    file -> {
                        if (Files.isRegularFile(file.toPath())) {
                            try (FileInputStream fis = new FileInputStream(file)) {
                                properties.load(fis);
                                LOGGER.info("Added settings from: {}", file);
                            } catch (FileNotFoundException e) {
                                LOGGER.info("No config file found at: {}", file);
                            } catch (IOException e) {
                                LOGGER.info("Failed to read config file at: {}", file);
                            }
                        } else {
                            LOGGER.info("Did not find configuration file: {}", file);
                        }
                    });
        }

        // Overlay system properties
        properties.putAll(System.getProperties());

        // Overlay environment variables
        properties.putAll(System.getenv());

        return properties.stringPropertyNames().stream()
                .collect(
                        HashMap::new,
                        (m, k) -> m.put(k, properties.getProperty(k)),
                        HashMap::putAll);
    }

    private static String getEnvOrProperty(String propertyName, String defaultValue) {
        String env = System.getenv(propertyName);
        if (env != null && !env.isEmpty()) {
            return env;
        }

        String property = System.getProperty(propertyName);
        if (property != null && !property.isEmpty()) {
            return property;
        }

        return defaultValue;
    }
}
