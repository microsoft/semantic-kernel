// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.openapi;

import com.azure.core.http.ContentType;
import com.azure.core.http.HttpClient;
import com.azure.core.http.HttpHeaders;
import com.azure.core.http.HttpMethod;
import com.azure.core.util.Header;
import com.azure.core.util.HttpClientOptions;
import com.fasterxml.jackson.core.JsonParser.Feature;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.OutputVariable;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.Paths;
import io.swagger.v3.oas.models.media.ArraySchema;
import io.swagger.v3.oas.models.media.BooleanSchema;
import io.swagger.v3.oas.models.media.IntegerSchema;
import io.swagger.v3.oas.models.media.MapSchema;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.media.NumberSchema;
import io.swagger.v3.oas.models.media.ObjectSchema;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.media.StringSchema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.parameters.RequestBody;
import io.swagger.v3.oas.models.servers.Server;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.apache.commons.text.StringEscapeUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SemanticKernelOpenAPIImporter {

    private static final Logger LOGGER = LoggerFactory.getLogger(
        SemanticKernelOpenAPIImporter.class);

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {

        private String pluginName;
        private String schema;
        private HttpHeaders httpHeaders;
        private HttpClient client;
        private Function<List<Server>, String> serverSelector;

        public Builder withPluginName(String pluginName) {
            this.pluginName = pluginName;
            return this;
        }

        public Builder withSchema(String schema) {
            this.schema = schema;
            return this;
        }

        public Builder withHttpHeaders(HttpHeaders httpHeaders) {
            this.httpHeaders = httpHeaders;
            return this;
        }

        public Builder withClient(HttpClient client) {
            this.client = client;
            return this;
        }

        public Builder withServerSelector(Function<List<Server>, String> serverSelector) {
            this.serverSelector = serverSelector;
            return this;
        }

        public Builder withServer(String serverUrl) {
            this.serverSelector = (ignore) -> serverUrl;
            return this;
        }

        public KernelPlugin build() {
            return SemanticKernelOpenAPIImporter.fromSchema(pluginName, schema, httpHeaders, client,
                serverSelector);
        }
    }

    public static KernelPlugin fromSchema(
        String pluginName,
        String schema,
        @Nullable HttpHeaders httpHeaders,
        @Nullable HttpClient client,
        @Nullable Function<List<Server>, String> serverSelector) {
        ParseOptions parseOptions = new ParseOptions();
        parseOptions.setResolve(true);
        parseOptions.setResolveFully(true);

        OpenAPI openAPI = new OpenAPIV3Parser().readContents(schema, null, parseOptions)
            .getOpenAPI();

        client = getHttpClient(httpHeaders, client);

        Paths paths = openAPI.getPaths();

        String serverUrl;

        if (serverSelector != null) {
            serverUrl = serverSelector.apply(openAPI.getServers());
        } else {
            serverUrl = openAPI.getServers().get(0).getUrl();
            if (openAPI.getServers().size() > 1) {
                LOGGER.warn("Multiple servers found, using the first one: {}", serverUrl);
            }
        }

        Map<String, KernelFunction<?>> functions = getFunctions(
            client,
            pluginName,
            paths,
            serverUrl,
            httpHeaders);

        return new KernelPlugin(
            pluginName,
            openAPI.getInfo().getDescription(),
            functions);
    }

    private static HttpClient getHttpClient(
        @Nullable HttpHeaders httpHeaders,
        @Nullable HttpClient client) {

        // Currently this does not apply as the Netty client does not obey the headers provided in the
        // HttpClientOptions, however they may do one day
        if (httpHeaders != null && client != null) {
            throw new IllegalArgumentException(
                "Both httpHeaders and client cannot be provided at the same time");
        }

        HttpClientOptions options = new HttpClientOptions();
        if (httpHeaders != null) {
            options.setHeaders(httpHeaders.stream()
                .map(header -> new Header(header.getName(), header.getValuesList()))
                .toList());
        }

        if (client == null) {
            client = HttpClient.createDefault(options);
        }
        return client;
    }

    private static Map<String, KernelFunction<?>> getFunctions(
        HttpClient client,
        String pluginName,
        Paths paths,
        String serverUrl,
        HttpHeaders headers) {
        return paths
            .entrySet()
            .stream()
            .flatMap((entry) -> {
                return formOperation(
                    client,
                    pluginName,
                    serverUrl,
                    entry.getKey(),
                    entry.getValue(),
                    headers)
                    .stream();
            })
            .collect(Collectors.toMap(KernelFunction::getName, (func) -> func));
    }

    private static List<KernelFunction<?>> formOperation(
        HttpClient client,
        String pluginName,
        String serverUrl,
        String path,
        PathItem pathItem,
        HttpHeaders headers) {

        List<KernelFunction<?>> plugins = new ArrayList<>();

        if (pathItem.getGet() != null) {
            var function = getKernelFunctionFromRequest(
                client,
                pluginName,
                serverUrl,
                path,
                pathItem,
                pathItem.getGet(),
                headers,
                HttpMethod.GET);

            plugins.add(function);
        }
        if (pathItem.getDelete() != null) {
            var function = getKernelFunctionFromRequest(
                client,
                pluginName,
                serverUrl,
                path,
                pathItem,
                pathItem.getDelete(),
                headers,
                HttpMethod.DELETE);

            plugins.add(function);
        }
        if (pathItem.getPost() != null) {
            var function = getKernelFunctionFromRequest(
                client,
                pluginName,
                serverUrl,
                path,
                pathItem,
                pathItem.getPost(),
                headers,
                HttpMethod.POST);

            plugins.add(function);
        }
        if (pathItem.getPut() != null) {
            var function = getKernelFunctionFromRequest(
                client,
                pluginName,
                serverUrl,
                path,
                pathItem,
                pathItem.getPut(),
                headers,
                HttpMethod.PUT);

            plugins.add(function);
        }
        if (pathItem.getPatch() != null) {
            var function = getKernelFunctionFromRequest(
                client,
                pluginName,
                serverUrl,
                path,
                pathItem,
                pathItem.getPatch(),
                headers,
                HttpMethod.PATCH);

            plugins.add(function);
        }
        if (pathItem.getOptions() != null) {
            var function = getKernelFunctionFromRequest(
                client,
                pluginName,
                serverUrl,
                path,
                pathItem,
                pathItem.getOptions(),
                headers,
                HttpMethod.OPTIONS);

            plugins.add(function);
        }
        if (pathItem.getHead() != null) {
            var function = getKernelFunctionFromRequest(
                client,
                pluginName,
                serverUrl,
                path,
                pathItem,
                pathItem.getHead(),
                headers,
                HttpMethod.HEAD);

            plugins.add(function);
        }
        if (pathItem.getTrace() != null) {
            var function = getKernelFunctionFromRequest(
                client,
                pluginName,
                serverUrl,
                path,
                pathItem,
                pathItem.getTrace(),
                headers,
                HttpMethod.TRACE);

            plugins.add(function);
        }

        return plugins;
    }

    private static @Nullable KernelFunction<Object> getKernelFunctionFromRequest(
        HttpClient client,
        String pluginName,
        String serverUrl,
        String path,
        PathItem pathItem,
        Operation operation,
        HttpHeaders headers,
        HttpMethod method) {

        List<InputVariable> variableList = getInputVariables(operation);
        OutputVariable<String> ov = getOutputVariable(operation);
        String description = getDescription(operation.getDescription());

        OpenAPIHttpRequestPlugin plugin = new OpenAPIHttpRequestPlugin(
            method,
            serverUrl,
            path,
            pathItem,
            client,
            headers,
            operation);

        RequestBody requestBody = operation.getRequestBody();

        if (requestBody != null) {
            if (requestBody.getContent().get(ContentType.APPLICATION_JSON) != null) {
                MediaType mediaType = requestBody.getContent().get(ContentType.APPLICATION_JSON);
                Schema<?> schema = mediaType.getSchema();

                String example = renderJsonExample(schema);

                try {
                    JsonNode parsed = new ObjectMapper()
                        .enable(Feature.ALLOW_TRAILING_COMMA)
                        .readTree(example);
                    example = parsed.get("root").toPrettyString();
                } catch (JsonProcessingException e) {
                    throw new RuntimeException("Failed to parse example JSON", e);
                }

                List<String> enums = getEnumValues(schema);

                variableList = new ArrayList<>(variableList);
                variableList.add(InputVariable.build(
                    "requestBody",
                    String.class,
                    "Example request body:\n" + example,
                    example,
                    enums,
                    true));

            } else {
                LOGGER.warn("No content type found for operation {}", operation.getOperationId());
            }
        }

        return buildKernelFunction(pluginName, plugin, operation, description, variableList, ov);
    }

    private static String renderJsonExample(Schema<?> schema) {
        StringBuilder stringBuilder = new StringBuilder();
        renderJsonExample(stringBuilder, "root", schema);
        return "{" + stringBuilder + "}";
    }

    private static void renderJsonExample(
        StringBuilder stringBuilder,
        String valueKey,
        Schema<?> schema) {

        if (schema.getExample() != null) {
            if (valueKey != null) {
                stringBuilder.append("\"").append(valueKey).append("\": ");
            }

            if (schema instanceof StringSchema) {
                stringBuilder.append("\"").append(schema.getExample().toString()).append("\",");
            } else {
                stringBuilder.append(schema.getExample().toString()).append(",");
            }
            return;
        }

        if (schema instanceof IntegerSchema ||
            schema instanceof StringSchema ||
            schema instanceof NumberSchema ||
            schema instanceof BooleanSchema) {

            String value;

            if (schema instanceof IntegerSchema) {
                value = "1";
            } else if (schema instanceof StringSchema) {
                if (schema.getEnum() != null && !schema.getEnum().isEmpty()) {
                    value = "\"" + schema.getEnum().get(0).toString() + "\"";
                } else {
                    value = "\"string\"";
                }
            } else if (schema instanceof NumberSchema) {
                value = "1.0";
            } else {
                value = "true";
            }

            if (valueKey != null) {
                stringBuilder.append("\"").append(valueKey).append("\": ");
            }
            stringBuilder.append(value).append(",");

        } else if (schema instanceof ObjectSchema objectSchema) {

            if (valueKey != null) {
                stringBuilder.append("\"").append(valueKey).append("\": ");
            }

            stringBuilder.append("{");

            objectSchema.getProperties().forEach((key, value) -> {
                renderJsonExample(stringBuilder, key, value);
            });
            stringBuilder.append("},");
        } else if (schema instanceof ArraySchema arraySchema) {

            if (valueKey != null) {
                stringBuilder.append("\"").append(valueKey).append("\": ");
            }

            stringBuilder.append("[");
            renderJsonExample(stringBuilder, null,
                arraySchema.getItems());
            stringBuilder.append("],");

        } else if (schema instanceof MapSchema) {
            throw new SKException("Not yet supported");
        } else {
            LOGGER.warn("Unsupported schema type {}", schema.getClass().getName());
        }
    }

    private static String renderXmlExample(Schema<?> schema) {
        StringBuilder stringBuilder = new StringBuilder();
        renderXmlExample(stringBuilder, null, schema);
        return stringBuilder.toString();
    }

    private static void renderXmlExample(StringBuilder stringBuilder, String valueKey,
        Schema<?> schema) {

        if (schema.getExample() != null) {
            stringBuilder.append("<").append(valueKey).append(">");
            stringBuilder.append(schema.getExample().toString());
            stringBuilder.append("</").append(valueKey).append(">");
            return;
        }

        if (schema instanceof IntegerSchema ||
            schema instanceof StringSchema ||
            schema instanceof NumberSchema ||
            schema instanceof BooleanSchema) {

            String value;

            if (schema instanceof IntegerSchema) {
                value = "1";
            } else if (schema instanceof StringSchema) {
                if (schema.getEnum() != null && !schema.getEnum().isEmpty()) {
                    value = schema.getEnum().get(0).toString();
                } else {
                    value = "string";
                }
            } else if (schema instanceof NumberSchema) {
                value = "1.0";
            } else {
                value = "true";
            }

            stringBuilder.append("<").append(valueKey).append(">");
            stringBuilder.append(value);
            stringBuilder.append("</").append(valueKey).append(">");
        } else if (schema instanceof ObjectSchema objectSchema) {

            String nameTag = "<" + schema.getXml().getName() + ">";
            String closingNameTag = "</" + schema.getXml().getName() + ">";

            stringBuilder.append(nameTag);
            objectSchema.getProperties().forEach((key, value) -> {
                renderXmlExample(stringBuilder, key, value);
            });
            stringBuilder.append(closingNameTag);
        } else if (schema instanceof ArraySchema arraySchema) {
            String nameTag = "<" + valueKey + ">";
            String closingNameTag = "</" + valueKey + ">";
            stringBuilder.append(nameTag);
            renderXmlExample(stringBuilder, arraySchema.getItems().getXml().getName(),
                arraySchema.getItems());
            stringBuilder.append(closingNameTag);
        } else if (schema instanceof MapSchema) {
            throw new SKException("Not yet supported");
        } else {
            LOGGER.warn("Unsupported schema type {}", schema.getClass().getName());
        }
    }

    private static KernelFunction<Object> buildKernelFunction(
        String pluginName,
        OpenAPIHttpRequestPlugin plugin,
        Operation operation,
        String description,
        List<InputVariable> variableList,
        OutputVariable<String> ov) {

        try {
            Method method = OpenAPIHttpRequestPlugin.class.getMethod("execute",
                KernelFunctionArguments.class);

            return KernelFunction
                .createFromMethod(method, plugin)
                .withFunctionName(operation.getOperationId())
                .withPluginName(pluginName)
                .withDescription(description)
                .withParameters(variableList)
                .withReturnParameter(ov)
                .build();
        } catch (NoSuchMethodException e) {
            return null;
        }
    }

    private static OutputVariable<String> getOutputVariable(Operation get) {
        return new OutputVariable<>(
            get.getDescription(),
            String.class);
    }

    private static @Nullable String getDescription(String get) {
        String description = get;
        if (description != null) {
            description = StringEscapeUtils.escapeXml11(description);
            description = description.replaceAll("\\n", "");
        }
        return description;
    }

    private static List<InputVariable> getInputVariables(Operation get) {
        List<InputVariable> variableList = List.of();
        if (get.getParameters() != null) {
            variableList = get
                .getParameters()
                .stream()
                .map(parameter -> {
                    Class<?> type = getType(parameter);

                    Object def = parameter.getSchema().getDefault();

                    String description = getDescription(parameter.getDescription());

                    List<String> enums = getEnumValues(parameter.getSchema());

                    return InputVariable.build(
                        parameter.getName(),
                        type,
                        description,
                        def != null ? def.toString() : null,
                        enums,
                        parameter.getRequired());
                })
                .collect(Collectors.toList());
        }
        return variableList;
    }

    private static List<String> getEnumValues(Schema<?> parameter) {
        if (parameter.getEnum() == null) {
            return null;
        }
        return parameter.getEnum()
            .stream()
            .map(Object::toString)
            .toList();
    }

    private static Class<?> getType(Parameter parameter) {
        Class<?> type = String.class;
        String t = parameter.getSchema().getType();
        if (t != null) {
            switch (t) {
                case "integer":
                    type = Integer.class;
                    break;
                case "number":
                    type = Double.class;
                    break;
                case "boolean":
                    type = Boolean.class;
                    break;
                case "array":
                    type = List.class;
                    break;

                // Not sure if we can support this
                case "null":
                    break;
                case "object":
                    break;
                default:
                    break;
            }
        }
        return type;
    }
}
