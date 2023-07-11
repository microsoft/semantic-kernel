// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import java.io.IOException;

import javax.annotation.Nullable;

public class OpenAISettings extends ClientSettings<OpenAISettings> {
    private static final String DEFAULT_CLIENT_ID = "openai";
    @Nullable private String key = null;
    @Nullable private String organizationId = null;

    private enum Property {
        OPEN_AI_KEY("key"),
        OPEN_AI_ORGANIZATION_ID("organizationid");
        private final String label;

        Property(String label) {
            this.label = label;
        }

        public String label() {
            return this.label;
        }
    }

    public String getKey() {
        if (key == null) {
            throw new RuntimeException("OpenAI key is not set");
        }
        return key;
    }

    public String getOrganizationId() {
        if (organizationId == null) {
            throw new RuntimeException("OpenAI organization id is not set");
        }
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
        this.organizationId =
                getSettingsValueFromFile(
                        path, Property.OPEN_AI_ORGANIZATION_ID.label(), clientSettingsId);
        return this;
    }

    @Override
    public boolean isValid() {
        return key != null && organizationId != null;
    }

    @Override
    public OpenAISettings fromSystemProperties() {
        return fromSystemProperties(DEFAULT_CLIENT_ID);
    }

    @Override
    public OpenAISettings fromSystemProperties(String clientSettingsId) {
        this.key =
                getSettingsValueFromSystemProperties(
                        Property.OPEN_AI_KEY.label(), clientSettingsId);
        this.organizationId =
                getSettingsValueFromSystemProperties(
                        Property.OPEN_AI_ORGANIZATION_ID.label(), clientSettingsId);
        return this;
    }
}
