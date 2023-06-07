package com.microsoft.semantickernel.util;

import java.io.IOException;

public class OpenAISettings extends ClientSettings<OpenAISettings> {
    private String key;
    private String organizationId;
    private static final String DEFAULT_CLIENT_ID = "openai";
    private enum Property {
        OPEN_AI_KEY("key"),
        OPEN_AI_ORGANIZATION_ID("organizationid");
        private final String label;
        Property (String label) {
            this.label = label;
        }
        public String label() {
            return this.label;
        }
    }

    public String getKey() {
        return key;
    }

    public String getOrganizationId() {
        return organizationId;
    }
    @Override
    public OpenAISettings fromEnv() {
        this.key = getSettingsValueFromEnv(Property.OPEN_AI_KEY.name());
        this.organizationId = getSettingsValueFromEnv(Property.OPEN_AI_ORGANIZATION_ID.name());
        return this;
    }

    @Override
    public OpenAISettings fromFile(String path) throws IOException {
        return fromFile(path, DEFAULT_CLIENT_ID);
    }

    @Override
    public OpenAISettings fromFile(String path, String clientSettingsId) throws IOException {
        this.key = getSettingsValueFromFile(path, Property.OPEN_AI_KEY.label(), clientSettingsId);
        this.organizationId = getSettingsValueFromFile(path, Property.OPEN_AI_ORGANIZATION_ID.label(), clientSettingsId);
        return this;
    }
}
