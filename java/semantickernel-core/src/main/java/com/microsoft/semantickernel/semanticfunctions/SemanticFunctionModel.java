// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class SemanticFunctionModel {
    @JsonProperty("name")
    private String name;

    @JsonProperty("template")
    private String template;

    @JsonProperty("template_format")
    private String templateFormat;

    @JsonProperty("description")
    private String description;

    @JsonProperty("input_variables")
    private List<VariableViewModel> inputVariables;

    @JsonProperty("output_variable")
    private VariableViewModel outputVariable;

    @JsonProperty("execution_settings")
    private List<ExecutionSettingsModel> executionSettings;

    public SemanticFunctionModel() {}

    public SemanticFunctionModel(
            String name,
            String template,
            String templateFormat,
            String description,
            List<VariableViewModel> inputVariables,
            VariableViewModel outputVariable,
            List<ExecutionSettingsModel> executionSettings) {
        this.name = name;
        this.template = template;
        this.templateFormat = templateFormat;
        this.description = description;
        this.inputVariables = inputVariables;
        this.outputVariable = outputVariable;
        this.executionSettings = executionSettings;
    }

    public static class VariableViewModel {
        @JsonProperty("name")
        private String name;

        @JsonProperty("type")
        private String type;

        @JsonProperty("description")
        private String description;

        @JsonProperty("default_value")
        private Object defaultValue;

        @JsonProperty("is_required")
        private boolean isRequired;

        public VariableViewModel() {}

        public VariableViewModel(
                String name,
                String type,
                String description,
                Object defaultValue,
                boolean isRequired) {
            this.name = name;
            this.type = type;
            this.description = description;
            this.defaultValue = defaultValue;
            this.isRequired = isRequired;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getType() {
            return type;
        }

        public void setType(String type) {
            this.type = type;
        }

        public String getDescription() {
            return description;
        }

        public void setDescription(String description) {
            this.description = description;
        }

        public Object getDefaultValue() {
            return defaultValue;
        }

        public void setDefaultValue(Object defaultValue) {
            this.defaultValue = defaultValue;
        }

        public boolean isRequired() {
            return isRequired;
        }

        public void setRequired(boolean required) {
            isRequired = required;
        }
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

    public List<VariableViewModel> getInputVariables() {
        return inputVariables;
    }

    public void setInputVariables(List<VariableViewModel> inputVariables) {
        this.inputVariables = inputVariables;
    }

    public VariableViewModel getOutputVariable() {
        return outputVariable;
    }

    public void setOutputVariable(VariableViewModel outputVariable) {
        this.outputVariable = outputVariable;
    }

    public List<ExecutionSettingsModel> getExecutionSettings() {
        return executionSettings;
    }

    public void setExecutionSettings(List<ExecutionSettingsModel> executionSettings) {
        this.executionSettings = executionSettings;
    }
}
