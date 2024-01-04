// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import com.microsoft.semantickernel.templateengine.semantickernel.DefaultPromptTemplate;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;

public class PromptTemplateConfig {

    private String name;

    private String template;

    private String templateFormat;

    private String description;

    private List<InputVariable> inputVariables;

    private OutputVariable outputVariable;

    private Map<String, PromptExecutionSettings> executionSettings;

    public PromptTemplateConfig(String template) {
        this(
            "default",
            template,
            "semantic-kernel",
            "",
            Collections.emptyList(),
            new OutputVariable("out", "string"),
            Collections.emptyMap()
        );
    }

    public PromptTemplateConfig(
        String name,
        String template,
        String templateFormat,
        String description,
        List<InputVariable> inputVariables,
        OutputVariable outputVariable,
        Map<String, PromptExecutionSettings> executionSettings) {
        this.name = name;
        this.template = template;
        this.templateFormat = templateFormat;
        this.description = description;
        this.inputVariables = inputVariables;
        if (inputVariables == null) {
            this.inputVariables = Collections.emptyList();
        }
        this.outputVariable = outputVariable;
        this.executionSettings = executionSettings;
    }

    @JsonCreator
    public PromptTemplateConfig(
        @JsonProperty("name")
        String name,
        @JsonProperty("template")
        String template,
        @JsonProperty("template_format")
        String templateFormat,
        @JsonProperty("description")
        String description,
        @JsonProperty("input_variables")
        List<InputVariable> inputVariables,
        @JsonProperty("output_variable")
        OutputVariable outputVariable,
        @JsonProperty("execution_settings")
        List<PromptExecutionSettings> executionSettings) {
        this.name = name;
        this.template = template;
        this.templateFormat = templateFormat;
        this.description = description;
        this.inputVariables = inputVariables;
        this.outputVariable = outputVariable;
        this.executionSettings = executionSettings
            .stream()
            .collect(Collectors.toMap(PromptExecutionSettings::getModelId, e -> e));
    }

    public List<KernelParameterMetadata> getKernelParametersMetadata() {
        if (inputVariables == null) {
            return Collections.emptyList();
        }
        return inputVariables
            .stream()
            .map(inputVariable -> new KernelParameterMetadata(
                inputVariable.getName(),
                inputVariable.getDescription(),
                inputVariable.getDefaultValue(),
                inputVariable.isRequired()
            ))
            .collect(Collectors.toList());
    }

    public KernelReturnParameterMetadata getKernelReturnParameterMetadata() {
        if (outputVariable == null) {
            return new KernelReturnParameterMetadata("");
        }

        return new KernelReturnParameterMetadata(
            outputVariable.getDescription()
        );
    }


    public static class ExecutionSettingsModel {

        @JsonProperty("model_id")
        private String modelId;

        @JsonProperty("model_id_pattern")
        private String modelIdPattern;

        @JsonProperty("service_id")
        private String serviceId;

        @JsonProperty("temperature")
        private String temperature;

        @JsonProperty("additional_properties")
        private final Map<String, Object> additionalProperties;

        public Object get(String propertyName) {
            return additionalProperties.get(propertyName);
        }

        public void set(String propertyName, Object value) {
            additionalProperties.put(propertyName, value);
        }

        public ExecutionSettingsModel() {
            this.additionalProperties = new HashMap<>();
        }

        public ExecutionSettingsModel(
            String modelId,
            String modelIdPattern,
            String serviceId,
            String temperature,
            Map<String, Object> additionalProperties) {
            this.modelId = modelId;
            this.modelIdPattern = modelIdPattern;
            this.serviceId = serviceId;
            this.temperature = temperature;
            this.additionalProperties = additionalProperties;
        }

        public String getModelId() {
            return modelId;
        }

        public void setModelId(String modelId) {
            this.modelId = modelId;
        }

        public String getModelIdPattern() {
            return modelIdPattern;
        }

        public void setModelIdPattern(String modelIdPattern) {
            this.modelIdPattern = modelIdPattern;
        }

        public String getServiceId() {
            return serviceId;
        }

        public void setServiceId(String serviceId) {
            this.serviceId = serviceId;
        }

        public String getTemperature() {
            return temperature;
        }

        public void setTemperature(String temperature) {
            this.temperature = temperature;
        }

        public Map<String, Object> getAdditionalProperties() {
            return additionalProperties;
        }
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
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

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<InputVariable> getInputVariables() {
        return inputVariables;
    }

    public void setInputVariables(List<InputVariable> inputVariables) {
        this.inputVariables = inputVariables;
    }

    public OutputVariable getOutputVariable() {
        return outputVariable;
    }

    public void setOutputVariable(OutputVariable outputVariable) {
        this.outputVariable = outputVariable;
    }

    public Map<String, PromptExecutionSettings> getExecutionSettings() {
        return executionSettings;
    }

    public void setExecutionSettings(Map<String, PromptExecutionSettings> executionSettings) {
        this.executionSettings = executionSettings;
    }

}
