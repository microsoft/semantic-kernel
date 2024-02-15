// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
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

    @Nullable
    private String name;
    private String template;
    private String templateFormat;
    @Nullable
    private String description;
    private List<InputVariable> inputVariables;
    @Nullable
    private OutputVariable outputVariable;
    private Map<String, PromptExecutionSettings> executionSettings;

    /**
     * Constructor for a prompt template config
     *
     * @param template Template string
     */
    public PromptTemplateConfig(String template) {
        this(
            CURRENT_SCHEMA,
            DEFAULT_CONFIG_NAME,
            template,
            SEMANTIC_KERNEL_TEMPLATE_FORMAT,
            "",
            Collections.emptyList(),
            new OutputVariable("out", String.class.getName()),
            Collections.emptyMap());
    }

    /**
     * Constructor for a prompt template config
     *
     * @param schema           Schema version
     * @param name             Name of the template
     * @param template         Template string
     * @param templateFormat   Template format
     * @param description      Description of the template
     * @param inputVariables   Input variables
     * @param outputVariable   Output variable
     * @param executionSettings Execution settings
     */
    @JsonCreator
    public PromptTemplateConfig(
        @JsonProperty("schema") int schema,
        @Nullable @JsonProperty("name") String name,
        @JsonProperty("template") String template,
        @Nullable @JsonProperty(value = "template_format", defaultValue = SEMANTIC_KERNEL_TEMPLATE_FORMAT) String templateFormat,
        @Nullable @JsonProperty("description") String description,
        @Nullable @JsonProperty("input_variables") List<InputVariable> inputVariables,
        @Nullable @JsonProperty("output_variable") OutputVariable outputVariable,
        @Nullable @JsonProperty("execution_settings") Map<String, PromptExecutionSettings> executionSettings) {
        this.name = name;
        this.template = template;
        if (templateFormat == null) {
            templateFormat = SEMANTIC_KERNEL_TEMPLATE_FORMAT;
        }
        this.templateFormat = templateFormat;
        this.description = description;
        if (inputVariables == null) {
            this.inputVariables = new ArrayList<>();
        } else {
            this.inputVariables = new ArrayList<>(inputVariables);
        }
        this.outputVariable = outputVariable;
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
     * @param inputVariables    Input variables
     * @param outputVariable    Output variable
     * @param executionSettings Execution settings
     */
    public PromptTemplateConfig(
        @Nullable String name,
        String template,
        @Nullable String templateFormat,
        @Nullable String description,
        @Nullable List<InputVariable> inputVariables,
        @Nullable OutputVariable outputVariable,
        @Nullable Map<String, PromptExecutionSettings> executionSettings) {
        this(
            CURRENT_SCHEMA,
            name,
            template,
            templateFormat,
            description,
            inputVariables,
            outputVariable,
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
            promptTemplate.inputVariables,
            promptTemplate.outputVariable,
            promptTemplate.executionSettings);
    }

    /**
     * Get the parameters metadata.
     *
     * @return The parameters metadata.
     */
    public List<KernelParameterMetadata<?>> getKernelParametersMetadata() {
        if (inputVariables == null) {
            return Collections.emptyList();
        }
        return inputVariables
            .stream()
            .map(inputVariable -> new KernelParameterMetadata<>(
                inputVariable.getName(),
                inputVariable.getDescription(),
                inputVariable.getTypeClass(),
                inputVariable.getDefaultValue(), inputVariable.isRequired()))
            .collect(Collectors.toList());
    }

    /**
     * Get the return parameter metadata.
     *
     * @return The return parameter metadata.
     */
    public KernelReturnParameterMetadata<?> getKernelReturnParameterMetadata() {
        if (outputVariable == null) {
            return new KernelReturnParameterMetadata<>("", String.class);
        }

        return new KernelReturnParameterMetadata<>(
            outputVariable.getDescription(),
            outputVariable.getType());
    }

    /**
     * Add an input variable to the prompt template config.
     *
     * @param inputVariable The input variable to add.
     * @return {@code this} prompt template config.
     */
    public PromptTemplateConfig addInputVariable(InputVariable inputVariable) {
        inputVariables.add(inputVariable);
        return this;
    }

    /**
     * Get the name of the prompt template config.
     * @return The name of the prompt template config.
     */
    @Nullable
    public String getName() {
        return name;
    }

    /**
     * Set the name of the prompt template config.
     * @param name The name of the prompt template config.
     * @return {@code this} prompt template config.
     */
    public PromptTemplateConfig setName(String name) {
        this.name = name;
        return this;
    }

    /**
     * Get the template of the prompt template config.
     * @return The template of the prompt template config.
     */
    public String getTemplate() {
        return template;
    }

    /**
     * Set the template of the prompt template config.
     * @param template The template of the prompt template config.
     * @return {@code this} prompt template config.
     */
    public PromptTemplateConfig setTemplate(String template) {
        this.template = template;
        return this;
    }

    /**
     * Get the template format of the prompt template config.
     * @return The template format of the prompt template config.
     */
    public String getTemplateFormat() {
        return templateFormat;
    }

    /**
     * Set the template format of the prompt template config.
     * @param templateFormat The template format of the prompt template config.
     * @return {@code this} prompt template config.
     */
    public PromptTemplateConfig setTemplateFormat(String templateFormat) {
        this.templateFormat = templateFormat;
        return this;
    }

    /**
     * Get the description of the prompt template config.
     * @return The description of the prompt template config.
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Set the description of the prompt template config.
     * @param description The description of the prompt template config.
     * @return {@code this} prompt template config.
     */
    public PromptTemplateConfig setDescription(String description) {
        this.description = description;
        return this;
    }

    /**
     * Get the inputVariables of the prompt template config.
     * @return The input variables of the prompt template config.
     */
    public List<InputVariable> getInputVariables() {
        return Collections.unmodifiableList(inputVariables);
    }

    /**
     * Set the inputVariables of the prompt template config.
     * @param inputVariables The input variables of the prompt template config.
     * @return {@code this} prompt template config.
     */
    public PromptTemplateConfig setInputVariables(List<InputVariable> inputVariables) {
        this.inputVariables = new ArrayList<>(inputVariables);
        return this;
    }

    /**
     * Get the output variable of the prompt template config.
     * @return The output variable of the prompt template config.
     */
    @Nullable
    public OutputVariable getOutputVariable() {
        return outputVariable;
    }

    /**
     * Set the output variable of the prompt template config.
     * @param outputVariable The output variable of the prompt template config.
     * @return {@code this} prompt template config.
     */
    public PromptTemplateConfig setOutputVariable(OutputVariable outputVariable) {
        this.outputVariable = outputVariable;
        return this;
    }

    /**
     * Get the prompt execution settings of the prompt template config.
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
     * Set the prompt execution settings of the prompt template config.
     * @param executionSettings The prompt execution settings of the prompt template config.
     * @return {@code this} prompt template config.
     */
    public PromptTemplateConfig setExecutionSettings(
        Map<String, PromptExecutionSettings> executionSettings) {
        this.executionSettings = new HashMap<>(executionSettings);
        return this;
    }

    /**
     * Deserialize the JSON string to a PromptTemplateConfig.
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

}
