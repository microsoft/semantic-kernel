package com.microsoft.semantickernel.aiservices.openai;

import com.azure.core.http.HttpHeaderName;
import com.azure.core.http.rest.RequestOptions;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import org.slf4j.Logger;

public final class OpenAIRequestSettings {

    private static final Logger LOGGER = org.slf4j.LoggerFactory.getLogger(
        OpenAIRequestSettings.class);

    private static final String SEMANTIC_KERNEL_VERSION_PROPERTY_NAME = "semantic-kernel.version";
    private static final String SEMANTIC_KERNEL_VERSION_PROPERTIES_FILE = "semantic-kernel-version.properties";
    private static final String version;

    static {
        version = loadVersion();
    }

    private static String loadVersion() {

        String version = "Java/unknown";

        try (InputStream settingsFile = OpenAIRequestSettings.class.getResourceAsStream(
            SEMANTIC_KERNEL_VERSION_PROPERTIES_FILE)) {

            Properties props = new Properties();
            props.load(settingsFile);
            if (props.containsKey(SEMANTIC_KERNEL_VERSION_PROPERTY_NAME)) {
                String skVersion = props.getProperty(SEMANTIC_KERNEL_VERSION_PROPERTY_NAME);
                if (skVersion != null && !skVersion.isEmpty()) {
                    return "Java/" + skVersion;
                }
            }
        } catch (IOException e) {
            //Ignore
            LOGGER.trace("Failed to load Semantic Kernel version from properties file", e);
        }
        return version;
    }

    public static RequestOptions getRequestOptions() {
        return new RequestOptions()
            .setHeader(HttpHeaderName.fromString("Semantic-Kernel-Version"), version);
    }
}
