package com.microsoft.semantickernel.aiservices.openai.azuresdk;


import com.azure.ai.openai.models.FunctionDefinition;
import com.azure.core.util.BinaryData;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.plugin.KernelParameterMetadata;

import javax.annotation.Nonnull;
import java.util.*;

/**
 * Represents a function that can be passed to the OpenAI API.
 */
public final class OpenAIFunction {
    private static final BinaryData ZERO_FUNCTION_PARAMETERS_SCHEMA;

    static {
        try {
            ZERO_FUNCTION_PARAMETERS_SCHEMA = BinaryData.fromObject(new ObjectMapper().readTree("{\"type\":\"object\",\"required\":[],\"properties\":{}}"));
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }
    private final String pluginName;
    private final String functionName;
    private final String description;
    private final List<OpenAIFunctionParameter> parameters;
    private final OpenAIFunctionReturnParameter returnParameter;

    /**
     * Initializes an OpenAIFunction.
     *
     * @param pluginName     The name of the plugin with which the function is associated, if any.
     * @param functionName   The name of the function.
     * @param description    A description of the function.
     * @param parameters     A list of parameters to the function, if any.
     * @param returnParameter The return parameter of the function, if any.
     */
    OpenAIFunction(String pluginName, @Nonnull String functionName, String description, List<OpenAIFunctionParameter> parameters, OpenAIFunctionReturnParameter returnParameter) {
        this.pluginName = pluginName;
        this.functionName = functionName;
        this.description = description;
        this.parameters = parameters;
        this.returnParameter = returnParameter;
    }

    /**
     * Gets the separator used between the plugin name and the function name, if a plugin name is present.
     *
     * @return The separator used between the plugin name and the function name.
     */
    public static String getNameSeparator() {
        return "_";
    }

    /**
     * Gets the name of the plugin with which the function is associated, if any.
     *
     * @return The name of the plugin, or null if no plugin is associated.
     */
    public String getPluginName() {
        return pluginName;
    }

    /**
     * Gets the name of the function.
     *
     * @return The name of the function.
     */
    public String getFunctionName() {
        return functionName;
    }

    /**
     * Gets the fully-qualified name of the function.
     *
     * @return The fully-qualified name of the function.
     */
    public String getFullyQualifiedName() {
        return (pluginName == null || pluginName.isEmpty()) ? functionName : pluginName + getNameSeparator() + functionName;
    }

    /**
     * Gets a description of the function.
     *
     * @return A description of the function.
     */
    public String getDescription() {
        return description;
    }

    /**
     * Gets a list of parameters to the function, if any.
     *
     * @return A list of parameters to the function, or null if no parameters are present.
     */
    public List<OpenAIFunctionParameter> getParameters() {
        return parameters;
    }

    /**
     * Gets the return parameter of the function, if any.
     *
     * @return The return parameter of the function, or null if no return parameter is present.
     */
    public OpenAIFunctionReturnParameter getReturnParameter() {
        return returnParameter;
    }

    public static OpenAIFunction fromKernelFunctionMetadata(KernelFunctionMetadata metadata, String pluginName) {
        List<KernelParameterMetadata> metadataParams = metadata.getParameters();
        List<OpenAIFunctionParameter> openAIParams = new ArrayList<>();

        metadataParams.forEach(param ->
            openAIParams.add(new OpenAIFunctionParameter(
                    param.getName(),
                    param.getDescription(),
                    param.isRequired(),
                    param.getType())
            )
        );

        return new OpenAIFunction(
                pluginName,
                metadata.getName(),
                metadata.getDescription(),
                openAIParams,
                new OpenAIFunctionReturnParameter(
                        metadata.getReturnParameter().getDescription(),
                        metadata.getReturnParameter().getParameterType()
                )
        );
    }

    private String getDefaultSchemaForParameter(String description) {
        if (description == null)
            return "{\"type\":\"string\"}";
        return String.format("{\"type\":\"string\", \"description\":\"%s\"}", description);
    }

    /**
     * Converts the OpenAIFunction representation to the Azure SDK's FunctionDefinition representation.
     *
     * @return A FunctionDefinition containing all the function information.
     */
    public FunctionDefinition toFunctionDefinition() {
        BinaryData resultParameters = ZERO_FUNCTION_PARAMETERS_SCHEMA;

        if (parameters != null && !parameters.isEmpty()) {
            Map<String, JsonNode> properties = new HashMap<>();
            List<String> required = new ArrayList<>();

            try {
                ObjectMapper objectMapper = new ObjectMapper();

                for (OpenAIFunctionParameter parameter : parameters) {
                    String parameterJsonSchema = getDefaultSchemaForParameter(parameter.getDescription());
                    properties.put(parameter.getName(), objectMapper.readTree(parameterJsonSchema));

                    if (parameter.isRequired()) {
                        required.add(parameter.getName());
                    }
                }

                String json = objectMapper.writeValueAsString(new Parameter("object", required, properties));
                resultParameters = BinaryData.fromObject(objectMapper.readTree(json));
            } catch (JsonProcessingException e) {
                throw new RuntimeException(e);
            }
        }

        FunctionDefinition functionDefinition = new FunctionDefinition(this.getFullyQualifiedName());
        functionDefinition.setDescription(description);
        functionDefinition.setParameters(resultParameters);

        return functionDefinition;
    }

    private static class Parameter {
        @JsonProperty("type")
        private String type;
        @JsonProperty("required")
        private List<String> required;
        @JsonProperty("properties")
        private Map<String, JsonNode> properties;

        public Parameter(String type, List<String> required, Map<String, JsonNode> properties) {
            this.type = type;
            this.required = required;
            this.properties = properties;
        }
    }
}

