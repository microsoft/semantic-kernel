// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.openapi;

import com.azure.core.http.ContentType;
import com.azure.core.http.HttpClient;
import com.azure.core.http.HttpHeaderName;
import com.azure.core.http.HttpHeaders;
import com.azure.core.http.HttpMethod;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.HttpResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.parameters.PathParameter;
import io.swagger.v3.oas.models.parameters.QueryParameter;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

/**
 * Plugin for making HTTP requests specifically to endpoints discovered via OpenAPI.
 */
public class OpenAPIHttpRequestPlugin {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenAPIHttpRequestPlugin.class);

    private final String serverUrl;
    private final String path;
    private final PathItem pathItem;
    private final HttpClient client;
    private final HttpMethod method;
    private final Operation operation;
    private final HttpHeaders httpHeaders;

    public OpenAPIHttpRequestPlugin(
        HttpMethod method,
        String serverUrl,
        String path,
        PathItem pathItem,
        HttpClient client,
        HttpHeaders httpHeaders,
        Operation operation) {
        this.method = method;
        this.serverUrl = serverUrl;
        this.path = path;
        this.pathItem = pathItem;
        this.client = client;
        this.httpHeaders = httpHeaders;
        this.operation = operation;
    }

    /**
     * Executes the HTTP request and return the body of the response.
     *
     * @param arguments The arguments to the http request.
     * @return The body of the response.
     */
    public Mono<String> execute(KernelFunctionArguments arguments) {
        String body = getBody(arguments);
        String query = buildQueryString(arguments);
        String path = buildQueryPath(arguments);

        String url;
        if (!query.isEmpty()) {
            url = serverUrl + path + "?" + query;
        } else {
            url = serverUrl + path;
        }

        HttpRequest request = new HttpRequest(method, url);

        HttpHeaders headers = new HttpHeaders();
        if (httpHeaders != null) {
            headers = headers.setAllHttpHeaders(httpHeaders);
        }

        if (body != null) {
            headers = headers.add(HttpHeaderName.CONTENT_TYPE, ContentType.APPLICATION_JSON);
            request = request.setBody(body);
        }

        if (headers.getSize() > 0) {
            request.setHeaders(headers);
        }

        LOGGER.debug("Executing {} {}", method.name(), url);
        if (body != null) {
            LOGGER.debug("Body: {}", body);
        }

        return client
            .send(request)
            .flatMap(response -> {
                if (response.getStatusCode() >= 400) {
                    return Mono.error(new RuntimeException(
                        "Request failed with status code: " + response.getStatusCode()));
                } else {
                    return Mono.just(response);
                }
            })
            .flatMap(HttpResponse::getBodyAsString)
            .doOnNext(response -> LOGGER.debug("Request response: {}", response));
    }

    private static @Nullable String getBody(KernelFunctionArguments arguments) {
        String body = null;
        if (arguments.containsKey("requestbody")) {
            ContextVariable<?> requestBody = arguments.get("requestbody");
            if (requestBody != null) {
                try {
                    JsonNode tree = new ObjectMapper().readTree(requestBody.getValue(String.class));
                    body = tree.toPrettyString();
                } catch (JsonProcessingException e) {
                    body = requestBody.getValue(String.class);
                }
            }
            arguments.remove("requestbody");
        }
        return body;
    }

    private String buildQueryPath(KernelFunctionArguments arguments) {
        return getParameterStreamOfArguments(arguments)
            .filter(p -> p instanceof PathParameter)
            .reduce(path, (path, parameter) -> {
                String name = parameter.getName();
                String rendered = getRenderedParameter(arguments, name);

                return path.replaceAll("\\{" + name + "}", rendered);
            }, (a, b) -> a + b);
    }

    private static String getRenderedParameter(
        KernelFunctionArguments arguments, String name) {
        ContextVariable<?> value = arguments.get(name);

        if (value == null) {
            throw new IllegalArgumentException("Missing value for path parameter: " + name);
        }
        String rendered = value.getValue(String.class);

        if (rendered == null) {
            throw new IllegalArgumentException("Path parameter value is null: " + name);
        }
        return URLEncoder.encode(rendered, StandardCharsets.US_ASCII);
    }

    private String buildQueryString(KernelFunctionArguments arguments) {
        return getParameterStreamOfArguments(arguments)
            .filter(p -> p instanceof QueryParameter)
            .map(parameter -> {
                String name = parameter.getName();
                String rendered = getRenderedParameter(arguments, name);
                return name + "=" + rendered;
            })
            .collect(Collectors.joining("&"));
    }

    private Stream<Parameter> getParameterStreamOfArguments(
        KernelFunctionArguments arguments) {
        if (operation.getParameters() == null) {
            return Stream.empty();
        }
        return arguments
            .keySet()
            .stream()
            .map(contextVariable -> pathItem
                .getGet()
                .getParameters()
                .stream()
                .filter(param -> param.getName().equalsIgnoreCase(contextVariable)).findFirst())
            .filter(Optional::isPresent)
            .map(Optional::get);
    }
}