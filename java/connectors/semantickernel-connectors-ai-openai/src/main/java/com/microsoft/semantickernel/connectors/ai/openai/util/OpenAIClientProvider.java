// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import static com.microsoft.semantickernel.exceptions.ConfigurationException.ErrorCodes.NoValidConfigurationsFound;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.ai.openai.models.NonAzureOpenAIKeyCredential;
import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.semantickernel.exceptions.ConfigurationException;

import org.slf4j.Logger;

import java.io.File;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

/**
 * Builds an OpenAI client instance, see {@link SettingsMap} documentation for details on how the
 * settings are loaded.
 *
 * <p>If clientType is not set via OPENAI_CLIENT_TYPE setting, then this will attempt to first
 * instantiate an OpenAI client, and if that fails, then it will attempt to instantiate an Azure
 * OpenAI client.
 */
public class OpenAIClientProvider {
    private static final Logger LOGGER =
            org.slf4j.LoggerFactory.getLogger(OpenAIClientProvider.class);

    public static final String OPENAI_CLIENT_TYPE = "OPENAI_CLIENT_TYPE";

    @Nullable private static final OpenAIClientProvider DEFAULT_INST;

    static {
        // Build a configuration following the default precedence
        OpenAIClientProvider DEFAULT_INST_TMP;
        try {
            DEFAULT_INST_TMP = buildProvider(null, null);
        } catch (ConfigurationException e) {
            LOGGER.error("Failed to load default settings", e);
            DEFAULT_INST_TMP = null;
        }
        DEFAULT_INST = DEFAULT_INST_TMP;
    }

    @Nullable private final ClientType clientType;
    private final Map<String, String> configuredSettings;

    /**
     * Create a new OpenAI client provider
     *
     * @param configuredSettings settings to use to configure the client
     * @param clientType client type
     */
    public OpenAIClientProvider(
            Map<String, String> configuredSettings, @Nullable ClientType clientType) {
        this.configuredSettings = Collections.unmodifiableMap(configuredSettings);
        this.clientType = clientType;
    }

    private static OpenAIClientProvider buildProvider(
            @Nullable List<File> propertyFileLocations, @Nullable ClientType clientType)
            throws ConfigurationException {
        Map<String, String> settings = getSettings(propertyFileLocations);

        if (clientType == null) {
            String clientValue = settings.get(OPENAI_CLIENT_TYPE);
            if (clientValue != null) {
                clientType = ClientType.valueOf(clientValue);
            }
        }

        return new OpenAIClientProvider(settings, clientType);
    }

    private static Map<String, String> getSettings(@Nullable List<File> propertyFileLocations)
            throws ConfigurationException {
        Map<String, String> settings;

        if (propertyFileLocations != null) {
            settings = SettingsMap.get(propertyFileLocations);
        } else {
            settings = SettingsMap.getDefault();
        }
        return settings;
    }

    /**
     * Get a client, overrides the default locations that are searched for settings
     *
     * @param propertyFileLocations locations to look for settings in
     * @param clientType client type
     * @return A client instance
     * @throws ConfigurationException if the settings are not found
     */
    public static OpenAIAsyncClient get(
            List<File> propertyFileLocations, @Nullable ClientType clientType)
            throws ConfigurationException {
        return buildProvider(propertyFileLocations, clientType).getAsyncClient();
    }

    /**
     * Get a client, overrides the default locations that are searched for settings
     *
     * @param propertyFileLocations locations to look for settings in
     * @return A client instance
     * @throws ConfigurationException if the settings are not found
     */
    public static OpenAIAsyncClient get(List<File> propertyFileLocations)
            throws ConfigurationException {
        return get(propertyFileLocations, null);
    }

    /**
     * Get a client, looks for settings in the default locations as defined by this class, PLUS the
     * additional locations provided
     *
     * @param propertyFileLocations additional locations to look for settings
     * @param clientType client type
     * @return A client instance
     */
    public static OpenAIAsyncClient getWithAdditional(
            List<File> propertyFileLocations, @Nullable ClientType clientType)
            throws ConfigurationException {
        Map<String, String> settings = SettingsMap.getWithAdditional(propertyFileLocations);

        if (clientType == null && settings.containsKey(OPENAI_CLIENT_TYPE)) {
            clientType = ClientType.valueOf(settings.get(OPENAI_CLIENT_TYPE));
        }

        return new OpenAIClientProvider(settings, clientType).getAsyncClient();
    }

    /**
     * Get a client, looks for settings in the default locations as defined by this class, PLUS the
     * additional locations provided
     *
     * @param propertyFileLocations additional locations to look for settings
     * @return A client instance
     */
    public static OpenAIAsyncClient getWithAdditional(List<File> propertyFileLocations)
            throws ConfigurationException {
        return getWithAdditional(propertyFileLocations, null);
    }

    /**
     * Builds an OpenAI client instance, see {@link SettingsMap} documentation for details on how
     * the settings are loaded.
     *
     * @return A client instance
     * @throws ConfigurationException If the settings are not found
     */
    public static OpenAIAsyncClient getClient() throws ConfigurationException {
        if (DEFAULT_INST == null) {
            throw new ConfigurationException(NoValidConfigurationsFound);
        }
        return DEFAULT_INST.getAsyncClient();
    }

    /**
     * Builds an OpenAI client instance, the settings for the client are loaded from the following
     * sources in the order of precedence (lower number in this list overrides a higher number):
     *
     * <ul>
     *   <li>1. Environment variables.
     *   <li>2. System properties.
     *   <li>3. Properties file set via CONF_PROPERTIES environment variable.
     *   <li>4. Properties file: ./conf.properties (Not used if CONF_PROPERTIES was set).
     *   <li>5. Properties file: ~/.sk/conf.properties (Not used if CONF_PROPERTIES was set).
     * </ul>
     *
     * <p>If clientType is not set via OPENAI_CLIENT_TYPE setting, then this will attempt to first
     * instantiate an OpenAI client, and if that fails, then it will attempt to instantiate an Azure
     * OpenAI client.
     *
     * @return A client instance
     * @throws ConfigurationException If the settings are not found
     */
    public OpenAIAsyncClient getAsyncClient() throws ConfigurationException {
        // No client type is specified, search for a valid client type
        if (clientType == null) {
            LOGGER.debug("No OpenAI client type specified, searching for a valid client type");
            try {
                LOGGER.debug("Trying OpenAI client");
                OpenAIAsyncClient client = buildOpenAIClient();
                LOGGER.debug("Successfully instantiated OpenAI client");
                return client;
            } catch (ConfigurationException e) {
                LOGGER.debug("No OpenAI client found");
            }

            try {
                LOGGER.debug("Trying Azure OpenAI client");
                OpenAIAsyncClient client = buildAzureOpenAIClient();
                LOGGER.debug("Successfully instantiated Azure OpenAI client");
                return client;
            } catch (ConfigurationException e) {
                LOGGER.debug("No Azure OpenAI client found");
                throw new ConfigurationException(NoValidConfigurationsFound);
            }
        } else {
            switch (clientType) {
                case OPEN_AI:
                    return buildOpenAIClient();
                case AZURE_OPEN_AI:
                    return buildAzureOpenAIClient();
                default:
                    throw new ConfigurationException(NoValidConfigurationsFound);
            }
        }
    }

    private OpenAIAsyncClient buildOpenAIClient() throws ConfigurationException {
        OpenAISettings settings = new OpenAISettings(configuredSettings);
        try {
            settings.assertIsValid();
        } catch (ConfigurationException e) {
            LOGGER.warn("Settings are not valid for OpenAI client");
            LOGGER.warn(e.getMessage());
            throw e;
        }

        return new OpenAIClientBuilder()
                .credential(new NonAzureOpenAIKeyCredential(settings.getKey()))
                .buildAsyncClient();
    }

    private OpenAIAsyncClient buildAzureOpenAIClient() throws ConfigurationException {
        AzureOpenAISettings settings = new AzureOpenAISettings(configuredSettings);

        try {
            settings.assertIsValid();
        } catch (ConfigurationException e) {
            LOGGER.warn("Could not instantiate Azure OpenAI client");
            LOGGER.warn(e.getMessage());
            throw e;
        }

        OpenAIClientBuilder builder =
                new OpenAIClientBuilder()
                        .endpoint(settings.getEndpoint())
                        .credential(new AzureKeyCredential(settings.getKey()));

        return builder.buildAsyncClient();
    }
}
