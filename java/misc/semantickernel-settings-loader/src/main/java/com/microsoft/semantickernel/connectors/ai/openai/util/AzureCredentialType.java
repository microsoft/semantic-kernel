// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import com.azure.core.credential.TokenCredential;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import java.io.File;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;
import org.slf4j.Logger;

/** Defines the type of azure credential used for authenticating to this resource */
public enum AzureCredentialType {
    KEY {
        @Nullable
        @Override
        public TokenCredential getTokenCredential() {
            return null;
        }
    },
    MANAGED_IDENTITY {
        @Nullable
        @Override
        public TokenCredential getTokenCredential() {
            if (classIsPresent("com.azure.identity.ManagedIdentityCredentialBuilder")) {
                return new com.azure.identity.ManagedIdentityCredentialBuilder().build();
            }
            return null;
        }
    },
    AZURE_CLI {
        @Nullable
        @Override
        public TokenCredential getTokenCredential() {
            if (classIsPresent("com.azure.identity.AzureCliCredentialBuilder")) {
                return new com.azure.identity.AzureCliCredentialBuilder().build();
            }
            return null;
        }
    };

    private static final Logger LOGGER =
            org.slf4j.LoggerFactory.getLogger(AzureCredentialType.class);

    /**
     * Create a TokenCredential instance.
     *
     * @return TokenCredential instance or null if not found
     */
    @Nullable
    public abstract TokenCredential getTokenCredential();

    /**
     * Create a TokenCredential instance, uses the default settings locations (see {@link
     * SettingsMap} for details).
     *
     * <p>Set the 'client.azureopenai.credentialtype' environment variable within settings to
     * determine the token type. {@link AzureCredentialType}
     *
     * @return TokenCredential instance or null if not found
     */
    @Nullable
    public static TokenCredential getCredential() throws ConfigurationException {
        return getCredential((List<File>) null);
    }

    /**
     * Create a TokenCredential instance, uses the provided settings locations (see {@link
     * SettingsMap} for details).
     *
     * <p>Set the 'client.azureopenai.credentialtype' environment variable within settings to
     * determine the token type. {@link AzureCredentialType}
     *
     * @return TokenCredential instance or null if not found
     */
    @Nullable
    public static TokenCredential getCredential(@Nullable List<File> propertyFileLocations)
            throws ConfigurationException {
        Map<String, String> settings = OpenAIClientProvider.getSettings(propertyFileLocations);
        return new AzureOpenAISettings(settings)
                .getAzureOpenAiCredentialsType()
                .getTokenCredential();
    }

    private static boolean classIsPresent(String className) {
        try {
            Class.forName(className, false, Thread.currentThread().getContextClassLoader());

            return true;
        } catch (ClassNotFoundException e) {
            LOGGER.warn(
                    "Requested Managed Identity or Azure CLI authentication, however the"
                            + " azure-identity library is not available on the classpath");
            return false;
        }
    }
}
