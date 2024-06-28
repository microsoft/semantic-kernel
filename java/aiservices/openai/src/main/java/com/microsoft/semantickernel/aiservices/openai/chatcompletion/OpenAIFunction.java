// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.models.FunctionDefinition;
import com.azure.core.util.BinaryData;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionMetadata;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

class OpenAIFunction {

    private final String pluginName;
    private final String name;
    private final FunctionDefinition functionDefinition;

    protected OpenAIFunction(
        @Nonnull String name,
        @Nonnull String pluginName,
        @Nonnull FunctionDefinition functionDefinition) {
        this.name = name;
        this.pluginName = pluginName;
        this.functionDefinition = functionDefinition;
    }

    public static OpenAIFunction build(KernelFunctionMetadata<?> metadata, String pluginName) {
        String name = metadata.getName();
        FunctionDefinition functionDefinition = toFunctionDefinition(metadata, pluginName);
        return new OpenAIFunction(name, pluginName, functionDefinition);
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
     * Gets the separator used between the plugin name and the function name, if a plugin name is
     * present.
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
    private static String getFullyQualifiedName(
        @Nullable String pluginName, String functionName) {
        return (pluginName == null || pluginName.isEmpty()) ? functionName
            : pluginName + getNameSeparator() + functionName;
    }

    /**
     * Converts a KernelFunctionMetadata representation to the SDK's FunctionDefinition
     * representation.
     *
     * @return A FunctionDefinition containing all the function information.
     */
    public static FunctionDefinition toFunctionDefinition(KernelFunctionMetadata<?> metadata,
        @Nullable String pluginName) {
        BinaryData resultParameters;

        Map<String, JsonNode> properties = new HashMap<>();
        List<String> required = new ArrayList<>();

        try {
            ObjectMapper objectMapper = new ObjectMapper();
            for (InputVariable parameter : metadata.getParameters()) {
                String parameterJsonSchema = getSchemaForFunctionParameter(parameter);

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

        public OpenAIFunctionParameter(
            String type,
            List<String> required,
            Map<String, JsonNode> properties) {
            this.type = type;
            this.required = Collections.unmodifiableList(required);
            this.properties = Collections.unmodifiableMap(properties);
        }

        @SuppressWarnings("UnusedMethod")
        public String getType() {
            return type;
        }

        @SuppressWarnings("UnusedMethod")
        public List<String> getRequired() {
            return required;
        }

        @SuppressWarnings("UnusedMethod")
        public Map<String, JsonNode> getProperties() {
            return properties;
        }
    }

    private static String getSchemaForFunctionParameter(@Nullable InputVariable parameter) {
        List<String> entries = new ArrayList<>();

        entries.add("\"type\":\"string\"");

        // Add description if present
        if (parameter != null && parameter.getDescription() != null && !parameter.getDescription()
            .isEmpty()) {
            String description = parameter.getDescription();
            description = description.replaceAll("\\r?\\n|\\r", "");
            description = description.replace("\"", "\\\"");

            description = String.format("\"description\":\"%s\"", description);
            entries.add(description);
        }

        // Add enum options if parameter is an enum
        if (parameter != null && parameter.getEnumValues() != null && !parameter.getEnumValues()
            .isEmpty()) {
            String enumEntry = parameter
                .getEnumValues()
                .stream()
                .map(Object::toString)
                .map(it -> "\"" + it + "\"")
                .collect(Collectors.joining(","));

            entries.add("\"enum\":[ " + enumEntry + " ]");
        }

        String schema = String.join(",", entries);

        return "{" + schema + "}";
    }
}
