package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.models.FunctionDefinition;
import com.azure.core.util.BinaryData;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.plugin.KernelParameterMetadata;

import java.util.Map;
import java.util.List;
import java.util.HashMap;
import java.util.ArrayList;

class OpenAIFunction {
    private final String pluginName;
    private final String name;
    private final FunctionDefinition functionDefinition;

    public OpenAIFunction(KernelFunctionMetadata<?> metadata, String pluginName) {
        this.name = metadata.getName();
        this.pluginName = pluginName;
        this.functionDefinition = toFunctionDefinition(metadata, pluginName);
    }

    public String getName() {
        return name;
    }

    public String getPluginName() {
        return pluginName;
    }

    public FunctionDefinition getFunctionDefinition() {
        return functionDefinition;
    }

    /**
     * Gets the separator used between the plugin name and the function name, if a plugin name is present.
     *
     * @return The separator used between the plugin name and the function name.
     */
    public static String getNameSeparator() {
        return "-";
    }

    /**
     * Gets the fully-qualified name of the function.
     *
     * @return The fully-qualified name of the function.
     */
    private static String getFullyQualifiedName(String pluginName, String functionName) {
        return (pluginName == null || pluginName.isEmpty()) ? functionName
            : pluginName + getNameSeparator() + functionName;
    }

    /**
     * Converts a KernelFunctionMetadata representation to the SDK's FunctionDefinition representation.
     *
     * @return A FunctionDefinition containing all the function information.
     */
    public static FunctionDefinition toFunctionDefinition(KernelFunctionMetadata<?> metadata,
        String pluginName) {
        BinaryData resultParameters;

        Map<String, JsonNode> properties = new HashMap<>();
        List<String> required = new ArrayList<>();

        try {
            ObjectMapper objectMapper = new ObjectMapper();
            for (KernelParameterMetadata<?> parameter : metadata.getParameters()) {
                String parameterJsonSchema = getSchemaForFunctionParameter(
                    parameter.getDescription());
                properties.put(parameter.getName(), objectMapper.readTree(parameterJsonSchema));

                if (parameter.isRequired()) {
                    required.add(parameter.getName());
                }
            }

            String json = objectMapper
                .writeValueAsString(new OpenAIFunctionParameter("object", required, properties));
            resultParameters = BinaryData.fromObject(objectMapper.readTree(json));
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }

        FunctionDefinition functionDefinition = new FunctionDefinition(
            getFullyQualifiedName(pluginName, metadata.getName()));
        functionDefinition.setDescription(metadata.getDescription());
        functionDefinition.setParameters(resultParameters);

        return functionDefinition;
    }

    private static class OpenAIFunctionParameter {
        @JsonProperty("type")
        private String type;
        @JsonProperty("required")
        private List<String> required;
        @JsonProperty("properties")
        private Map<String, JsonNode> properties;

        public OpenAIFunctionParameter(String type, List<String> required,
            Map<String, JsonNode> properties) {
            this.type = type;
            this.required = required;
            this.properties = properties;
        }
    }

    private static String getSchemaForFunctionParameter(String description) {
        if (description == null)
            return "{\"type\":\"string\"}";
        return String.format("{\"type\":\"string\", \"description\":\"%s\"}", description);
    }
}
