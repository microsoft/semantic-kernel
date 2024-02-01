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

@JsonIgnoreProperties(ignoreUnknown = true)
public class PromptTemplateConfig {

    public static final int CURRENT_SCHEMA = 1;
    public static final String DEFAULT_CONFIG_NAME = "default";
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

    public static final String SEMANTIC_KERNEL_TEMPLATE_FORMAT = "semantic-kernel";

    public PromptTemplateConfig(String template) {
        this(
            CURRENT_SCHEMA,
            DEFAULT_CONFIG_NAME,
            template,
            SEMANTIC_KERNEL_TEMPLATE_FORMAT,
            "",
            Collections.emptyList(),
            new OutputVariable("out", String.class.getName()),
            Collections.emptyMap()
        );
    }

    @JsonCreator
    public PromptTemplateConfig(
        @JsonProperty("schema")
        int schema,
        @Nullable
        @JsonProperty("name")
        String name,
        @JsonProperty("template")
        String template,
        @Nullable
        @JsonProperty(
            value = "template_format",
            defaultValue = SEMANTIC_KERNEL_TEMPLATE_FORMAT)
        String templateFormat,
        @Nullable
        @JsonProperty("description")
        String description,
        @Nullable
        @JsonProperty("input_variables")
        List<InputVariable> inputVariables,
        @Nullable
        @JsonProperty("output_variable")
        OutputVariable outputVariable,
        @Nullable
        @JsonProperty("execution_settings")
        Map<String, PromptExecutionSettings> executionSettings) {
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
        @Nullable
        String name,
        String template,
        @Nullable
        String templateFormat,
        @Nullable
        String description,
        @Nullable
        List<InputVariable> inputVariables,
        @Nullable
        OutputVariable outputVariable,
        @Nullable
        Map<String, PromptExecutionSettings> executionSettings) {
        this(
            CURRENT_SCHEMA,
            name,
            template,
            templateFormat,
            description,
            inputVariables,
            outputVariable,
            executionSettings
        );
    }

    public PromptTemplateConfig(PromptTemplateConfig promptTemplate) {
        this(
            promptTemplate.name,
            promptTemplate.template,
            promptTemplate.templateFormat,
            promptTemplate.description,
            promptTemplate.inputVariables,
            promptTemplate.outputVariable,
            promptTemplate.executionSettings
        );
    }

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
                inputVariable.getDefaultValue(), inputVariable.isRequired()
            ))
            .collect(Collectors.toList());
    }

    public KernelReturnParameterMetadata<?> getKernelReturnParameterMetadata() {
        if (outputVariable == null) {
            return new KernelReturnParameterMetadata<>("", String.class);
        }

        return new KernelReturnParameterMetadata<>(
            outputVariable.getDescription(),
            outputVariable.getType()
        );
    }

    public void addInputVariable(InputVariable inputVariable) {
        inputVariables.add(inputVariable);
    }

    @Nullable
    public String getName() {
        return name;
    }

    public PromptTemplateConfig setName(String name) {
        this.name = name;
        return this;
    }

    public String getTemplate() {
        return template;
    }

    public void setTemplate(String template) {
        this.template = template;
    }

    public String getTemplateFormat() {
        return templateFormat;
    }

    public void setTemplateFormat(String templateFormat) {
        this.templateFormat = templateFormat;
    }

    @Nullable
    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<InputVariable> getInputVariables() {
        return Collections.unmodifiableList(inputVariables);
    }

    public void setInputVariables(List<InputVariable> inputVariables) {
        this.inputVariables = new ArrayList<>(inputVariables);
    }

    @Nullable
    public OutputVariable getOutputVariable() {
        return outputVariable;
    }

    public void setOutputVariable(OutputVariable outputVariable) {
        this.outputVariable = outputVariable;
    }

    @Nullable
    public Map<String, PromptExecutionSettings> getExecutionSettings() {
        if (executionSettings != null) {
            return Collections.unmodifiableMap(executionSettings);
        }
        return null;
    }


    public void setExecutionSettings(Map<String, PromptExecutionSettings> executionSettings) {
        this.executionSettings = new HashMap<>(executionSettings);
    }

    public static PromptTemplateConfig parseFromJson(String json) throws SKException {
        try {
            return new ObjectMapper().readValue(json, PromptTemplateConfig.class);
        } catch (JsonProcessingException e) {
            throw new SKException("Unable to parse prompt template config", e);
        }
    }

}
