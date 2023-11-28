// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import java.util.ArrayList;
import javax.annotation.Nullable;

/** Prompt template configuration */
@JsonIgnoreProperties(ignoreUnknown = true)
public class PromptTemplateConfig {

    private final CompletionRequestSettings completionRequestSettings;
    private final InputConfig input;
    private final int schema;
    private final String type; // { get; set; } = "completion";
    private final String description;

    public PromptTemplateConfig() {
        this("", "", null);
    }

    public PromptTemplateConfig(CompletionRequestSettings completionRequestSettings) {
        this(1, "", "", completionRequestSettings, new InputConfig(new ArrayList<>()));
    }

    public PromptTemplateConfig(
            String description,
            String type,
            @Nullable CompletionRequestSettings completionRequestSettings) {
        this(1, description, type, completionRequestSettings, new InputConfig(new ArrayList<>()));
    }

    @JsonCreator
    public PromptTemplateConfig(
            @JsonProperty("schema") int schema,
            @JsonProperty("description") String description,
            @JsonProperty("type") String type,
            @Nullable @JsonProperty("completion")
                    CompletionRequestSettings completionRequestSettings,
            @Nullable @JsonProperty("input") InputConfig input) {
        if (completionRequestSettings == null) {
            completionRequestSettings = new CompletionRequestSettings();
        }
        this.schema = schema;
        this.description = description;
        this.type = type;
        this.completionRequestSettings = completionRequestSettings;
        if (input == null) {
            input = new InputConfig(new ArrayList<>());
        }
        this.input = input;
    }

    /**
     * Description
     *
     * @return Description
     */
    public String getDescription() {
        return description;
    }

    /**
     * A returns the configuration for the text completion
     *
     * @return CompletionRequestSettings
     */
    public CompletionRequestSettings getCompletionRequestSettings() {
        return completionRequestSettings;
    }

    public int getSchema() {
        return schema;
    }

    public String getType() {
        return type;
    }

    public InputConfig getInput() {
        return input;
    }
}
