// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import javax.annotation.Nullable;

/**
 * Metadata for a prompt template.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class PromptTemplateConfig {

    /**
     * The current prompt template config schema version.
     */
    public static final int CURRENT_SCHEMA = 1;

    /**
     * The default name for a prompt template config.
     */
    public static final String DEFAULT_CONFIG_NAME = "default";

    /**
     * The default template format for a prompt template config.
     */
    public static final String SEMANTIC_KERNEL_TEMPLATE_FORMAT = "semantic-kernel";

    private final int schema;
    @Nullable
    private final String name;
    @Nullable
    private final String template;
    private final String templateFormat;
    @Nullable
    private final String description;
    private final List<KernelInputVariable> kernelInputVariables;
    @Nullable
    private final KernelOutputVariable kernelOutputVariable;
    private final Map<String, PromptExecutionSettings> executionSettings;

    /**
     * Constructor for a prompt template config
     *
     * @param template Template string
     */
    protected PromptTemplateConfig(String template) {
        this(
            CURRENT_SCHEMA,
            DEFAULT_CONFIG_NAME,
            template,
            SEMANTIC_KERNEL_TEMPLATE_FORMAT,
            "",
            Collections.emptyList(),
            new KernelOutputVariable(String.class.getName(), "out"),
            Collections.emptyMap());
    }

    /**
     * Constructor for a prompt template config
     *
     * @param schema            Schema version
     * @param name              Name of the template
     * @param template          Template string
     * @param templateFormat    Template format
     * @param description       Description of the template
     * @param kernelInputVariables    Input variables
     * @param kernelOutputVariable    Output variable
     * @param executionSettings Execution settings
     */
    @JsonCreator
    public PromptTemplateConfig(
        @JsonProperty("schema") int schema,
        @Nullable @JsonProperty("name") String name,
        @Nullable @JsonProperty("template") String template,
        @Nullable @JsonProperty(value = "template_format", defaultValue = SEMANTIC_KERNEL_TEMPLATE_FORMAT) String templateFormat,
        @Nullable @JsonProperty("description") String description,
        @Nullable @JsonProperty("input_variables") List<KernelInputVariable> kernelInputVariables,
        @Nullable @JsonProperty("output_variable") KernelOutputVariable kernelOutputVariable,
        @Nullable @JsonProperty("execution_settings") Map<String, PromptExecutionSettings> executionSettings) {
        this.schema = schema;
        this.name = name;
        this.template = template;
        if (templateFormat == null) {
            templateFormat = SEMANTIC_KERNEL_TEMPLATE_FORMAT;
        }
        this.templateFormat = templateFormat;
        this.description = description;
        if (kernelInputVariables == null) {
            this.kernelInputVariables = new ArrayList<>();
        } else {
            this.kernelInputVariables = new ArrayList<>(kernelInputVariables);
        }
        this.kernelOutputVariable = kernelOutputVariable != null
            ? kernelOutputVariable
            : new KernelOutputVariable(String.class.getName(), "out");
        if (executionSettings == null) {
            this.executionSettings = new HashMap<>();
        } else {
            this.executionSettings = new HashMap<>(executionSettings);
        }
    }

    /**
     * Constructor for a prompt template config
     *
     * @param name              Name of the template
     * @param template          Template string
     * @param templateFormat    Template format
     * @param description       Description of the template
     * @param kernelInputVariables    Input variables
     * @param kernelOutputVariable    Output variable
     * @param executionSettings Execution settings
     */
    protected PromptTemplateConfig(
        @Nullable String name,
        @Nullable String template,
        @Nullable String templateFormat,
        @Nullable String description,
        @Nullable List<KernelInputVariable> kernelInputVariables,
        @Nullable KernelOutputVariable kernelOutputVariable,
        @Nullable Map<String, PromptExecutionSettings> executionSettings) {
        this(
            CURRENT_SCHEMA,
            name,
            template,
            templateFormat,
            description,
            kernelInputVariables,
            kernelOutputVariable,
            executionSettings);
    }

    /**
     * Copy constructor.
     *
     * @param promptTemplate The prompt template to copy.
     */
    public PromptTemplateConfig(PromptTemplateConfig promptTemplate) {
        this(
            promptTemplate.name,
            promptTemplate.template,
            promptTemplate.templateFormat,
            promptTemplate.description,
            promptTemplate.kernelInputVariables,
            promptTemplate.kernelOutputVariable,
            promptTemplate.executionSettings);
    }

    /**
     * Deserialize the JSON string to a PromptTemplateConfig.
     *
     * @param json The JSON string to parse
     * @return The PromptTemplateConfig object
     * @throws SKException If the prompt template config cannot be deserialized.
     */
    public static PromptTemplateConfig parseFromJson(String json) throws SKException {
        try {
            return new ObjectMapper().readValue(json, PromptTemplateConfig.class);
        } catch (JsonProcessingException e) {
            throw new SKException("Unable to parse prompt template config", e);
        }
    }

    /**
     * Create a builder for a prompt template config.
     *
     * @return The prompt template config builder.
     */
    public static Builder builder() {
        return new Builder();
    }

    /**
     * Create a builder for a prompt template config, where the constructed template will be
     * considered the default to be used if no other config is selected.
     *
     * @return The default prompt template config.
     */
    public static Builder defaultTemplateBuilder() {
        return new Builder()
            .withName(DEFAULT_CONFIG_NAME);
    }

    /**
     * Get the parameters metadata.
     *
     * @return The parameters metadata.
     */
    public List<KernelInputVariable> getKernelParametersMetadata() {
        if (kernelInputVariables == null) {
            return Collections.emptyList();
        }
        return Collections.unmodifiableList(kernelInputVariables);
    }

    /**
     * Get the return parameter metadata.
     *
     * @return The return parameter metadata.
     */
    public KernelOutputVariable<?> getKernelReturnParameterMetadata() {
        if (kernelOutputVariable == null) {
            return new KernelOutputVariable<>("", String.class);
        }

        return new KernelOutputVariable<>(
            kernelOutputVariable.getDescription(),
            kernelOutputVariable.getType());
    }

    /**
     * Get the name of the prompt template config.
     *
     * @return The name of the prompt template config.
     */
    @Nullable
    public String getName() {
        return name;
    }

    /**
     * Get the template of the prompt template config.
     *
     * @return The template of the prompt template config.
     */
    @Nullable
    public String getTemplate() {
        return template;
    }

    /**
     * Get the description of the prompt template config.
     *
     * @return The description of the prompt template config.
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Get the inputVariables of the prompt template config.
     *
     * @return The input variables of the prompt template config.
     */
    public List<KernelInputVariable> getInputVariables() {
        return Collections.unmodifiableList(kernelInputVariables);
    }

    /**
     * Get the output variable of the prompt template config.
     *
     * @return The output variable of the prompt template config.
     */
    @Nullable
    public KernelOutputVariable getOutputVariable() {
        return kernelOutputVariable;
    }

    /**
     * Get the prompt execution settings of the prompt template config.
     *
     * @return The prompt execution settings of the prompt template config.
     */
    @Nullable
    public Map<String, PromptExecutionSettings> getExecutionSettings() {
        if (executionSettings != null) {
            return Collections.unmodifiableMap(executionSettings);
        }
        return null;
    }

    /**
     * Get the template format of the prompt template config.
     *
     * @return The template format of the prompt template config.
     */
    public String getTemplateFormat() {
        return templateFormat;
    }

    /**
     * Get the schema version of the prompt template config.
     *
     * @return The schema version of the prompt template config.
     */
    public int getSchema() {
        return schema;
    }

    /**
     * Create a builder for a prompt template config which is a clone of the current object.
     *
     * @return The prompt template config builder.
     */
    public Builder copy() {
        return new Builder(this);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, template, templateFormat, description, kernelInputVariables,
            kernelOutputVariable, executionSettings);
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (!getClass().isInstance(obj)) {
            return false;
        }
        final PromptTemplateConfig other = (PromptTemplateConfig) obj;
        if (!Objects.equals(this.name, other.name)) {
            return false;
        }
        if (!Objects.equals(this.template, other.template)) {
            return false;
        }
        if (!Objects.equals(this.description, other.description)) {
            return false;
        }
        if (!Objects.equals(this.templateFormat, other.templateFormat)) {
            return false;
        }
        if (!Objects.equals(this.kernelInputVariables, other.kernelInputVariables)) {
            return false;
        }
        if (!Objects.equals(this.kernelOutputVariable, other.kernelOutputVariable)) {
            return false;
        }
        return Objects.equals(this.executionSettings, other.executionSettings);
    }

    /**
     * Builder for a prompt template config.
     */
    public static class Builder {

        @Nullable
        private String name;
        @Nullable
        private String template;
        private String templateFormat = SEMANTIC_KERNEL_TEMPLATE_FORMAT;
        @Nullable
        private String description = null;
        private List<KernelInputVariable> kernelInputVariables = new ArrayList<>();
        @Nullable
        private KernelOutputVariable kernelOutputVariable;
        private Map<String, PromptExecutionSettings> executionSettings = new HashMap<>();

        private Builder() {
        }

        private Builder(PromptTemplateConfig promptTemplateConfig) {
            this.name = promptTemplateConfig.name;
            this.template = promptTemplateConfig.template;
            this.templateFormat = promptTemplateConfig.templateFormat;
            this.description = promptTemplateConfig.description;
            this.kernelInputVariables = new ArrayList<>(promptTemplateConfig.kernelInputVariables);
            this.kernelOutputVariable = promptTemplateConfig.kernelOutputVariable;
            this.executionSettings = new HashMap<>(promptTemplateConfig.executionSettings);
        }

        /**
         * Set the name of the prompt template config.
         *
         * @param name The name of the prompt template config.
         * @return {@code this} prompt template config.
         */
        public Builder withName(String name) {
            this.name = name;
            return this;
        }

        /**
         * Add an input variable to the prompt template config.
         *
         * @param kernelInputVariable The input variable to add.
         * @return {@code this} prompt template config.
         */
        public Builder addInputVariable(KernelInputVariable kernelInputVariable) {
            kernelInputVariables.add(kernelInputVariable);
            return this;
        }

        /**
         * Set the template of the prompt template config.
         *
         * @param template The template of the prompt template config.
         * @return {@code this} prompt template config.
         */
        public Builder withTemplate(String template) {
            this.template = template;
            return this;
        }

        /**
         * Set the description of the prompt template config.
         *
         * @param description The description of the prompt template config.
         * @return {@code this} prompt template config.
         */
        public Builder withDescription(String description) {
            this.description = description;
            return this;
        }

        /**
         * Set the template format of the prompt template config.
         *
         * @param templateFormat The template format of the prompt template config.
         * @return {@code this} prompt template config.
         */
        public Builder withTemplateFormat(String templateFormat) {
            this.templateFormat = templateFormat;
            return this;
        }

        /**
         * Set the inputVariables of the prompt template config.
         *
         * @param kernelInputVariables The input variables of the prompt template config.
         * @return {@code this} prompt template config.
         */
        public Builder withInputVariables(List<KernelInputVariable> kernelInputVariables) {
            this.kernelInputVariables = new ArrayList<>(kernelInputVariables);
            return this;
        }

        /**
         * Set the output variable of the prompt template config.
         *
         * @param kernelOutputVariable The output variable of the prompt template config.
         * @return {@code this} prompt template config.
         */
        public Builder withOutputVariable(KernelOutputVariable<?> kernelOutputVariable) {
            this.kernelOutputVariable = kernelOutputVariable;
            return this;
        }

        /**
         * Set the prompt execution settings of the prompt template config.
         *
         * @param executionSettings The prompt execution settings of the prompt template config.
         * @return {@code this} prompt template config.
         */
        public Builder withExecutionSettings(
            Map<String, PromptExecutionSettings> executionSettings) {
            this.executionSettings = new HashMap<>(executionSettings);
            return this;
        }

        /**
         * Build the prompt template config.
         *
         * @return The prompt template config.
         */
        public PromptTemplateConfig build() {
            return new PromptTemplateConfig(
                name,
                template,
                templateFormat,
                description,
                kernelInputVariables,
                kernelOutputVariable,
                executionSettings);
        }
    }
}
