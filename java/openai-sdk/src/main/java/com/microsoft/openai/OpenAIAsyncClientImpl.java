// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.openai;

import com.azure.ai.openai.models.*;
import com.azure.core.annotation.*;
import com.azure.core.exception.ClientAuthenticationException;
import com.azure.core.exception.HttpResponseException;
import com.azure.core.exception.ResourceModifiedException;
import com.azure.core.exception.ResourceNotFoundException;
import com.azure.core.http.HttpHeaderName;
import com.azure.core.http.HttpPipeline;
import com.azure.core.http.HttpPipelineBuilder;
import com.azure.core.http.policy.CookiePolicy;
import com.azure.core.http.policy.RetryPolicy;
import com.azure.core.http.policy.UserAgentPolicy;
import com.azure.core.http.rest.RequestOptions;
import com.azure.core.http.rest.Response;
import com.azure.core.http.rest.RestProxy;
import com.azure.core.util.*;
import com.azure.core.util.serializer.JacksonAdapter;
import com.azure.core.util.serializer.SerializerAdapter;

import reactor.core.publisher.Mono;

class OpenAIAsyncClientImpl implements OpenAIAsyncClient {
    private final OpenAIClientService service;
    private final String endpoint;

    public String getEndpoint() {
        return this.endpoint;
    }

    private final SerializerAdapter serializerAdapter;

    public SerializerAdapter getSerializerAdapter() {
        return this.serializerAdapter;
    }

    private String apiKey;

    public OpenAIAsyncClientImpl(String endpoint, String apiKey) {
        this(
                new HttpPipelineBuilder()
                        .policies(new UserAgentPolicy(), new RetryPolicy(), new CookiePolicy())
                        .build(),
                JacksonAdapter.createDefaultSerializerAdapter(),
                endpoint);
        this.apiKey = apiKey;
    }

    public OpenAIAsyncClientImpl(
            HttpPipeline httpPipeline, SerializerAdapter serializerAdapter, String endpoint) {
        this.serializerAdapter = serializerAdapter;
        this.endpoint = endpoint;
        this.service =
                RestProxy.create(
                        OpenAIClientService.class, httpPipeline, this.getSerializerAdapter());
    }

    @Override
    public Mono<Embeddings> getEmbeddings(
            String deploymentId, EmbeddingsOptions embeddingsOptions) {
        final String accept = "application/json";
        return FluxUtil.withContext(
                        context ->
                                service.getEmbeddings(
                                        this.getEndpoint(),
                                        accept,
                                        BinaryData.fromObject(embeddingsOptions),
                                        new RequestOptions()
                                                .addHeader(
                                                        HttpHeaderName.AUTHORIZATION,
                                                        "Bearer " + this.apiKey),
                                        context))
                .flatMap(FluxUtil::toMono)
                .map(protocolMethodData -> protocolMethodData.toObject(Embeddings.class));
    }

    @Override
    public Mono<Completions> getCompletions(
            String deploymentId, CompletionsOptions completionsOptions) {
        final String accept = "application/json";
        return FluxUtil.withContext(
                        context ->
                                service.getCompletions(
                                        this.getEndpoint(),
                                        accept,
                                        BinaryData.fromObject(completionsOptions),
                                        new RequestOptions()
                                                .addHeader(
                                                        HttpHeaderName.AUTHORIZATION,
                                                        "Bearer " + this.apiKey),
                                        context))
                .flatMap(FluxUtil::toMono)
                .map(protocolMethodData -> protocolMethodData.toObject(Completions.class));
    }

    @Override
    public Mono<ChatCompletions> getChatCompletions(
            String deploymentId, ChatCompletionsOptions chatCompletionsOptions) {
        final String accept = "application/json";
        return FluxUtil.withContext(
                        context ->
                                service.getChatCompletions(
                                        this.getEndpoint(),
                                        accept,
                                        BinaryData.fromObject(chatCompletionsOptions),
                                        new RequestOptions()
                                                .addHeader(
                                                        HttpHeaderName.AUTHORIZATION,
                                                        "Bearer " + this.apiKey),
                                        context))
                .flatMap(FluxUtil::toMono)
                .map(protocolMethodData -> protocolMethodData.toObject(ChatCompletions.class));
    }

    /**
     * The interface defining all the services for OpenAIAPI to be used by the proxy service to
     * perform REST calls.
     */
    @Host("{endpoint}")
    @ServiceInterface(name = "OpenAIClient")
    public interface OpenAIClientService {

        @Post("/embeddings")
        @ExpectedResponses({200})
        @UnexpectedResponseExceptionType(
                value = ClientAuthenticationException.class,
                code = {401})
        @UnexpectedResponseExceptionType(
                value = ResourceNotFoundException.class,
                code = {404})
        @UnexpectedResponseExceptionType(
                value = ResourceModifiedException.class,
                code = {409})
        @UnexpectedResponseExceptionType(HttpResponseException.class)
        Mono<Response<BinaryData>> getEmbeddings(
                @HostParam("endpoint") String endpoint,
                @HeaderParam("accept") String accept,
                @BodyParam("application/json") BinaryData embeddingsOptions,
                RequestOptions requestOptions,
                Context context);

        @Post("/completions")
        @ExpectedResponses({200})
        @UnexpectedResponseExceptionType(
                value = ClientAuthenticationException.class,
                code = {401})
        @UnexpectedResponseExceptionType(
                value = ResourceNotFoundException.class,
                code = {404})
        @UnexpectedResponseExceptionType(
                value = ResourceModifiedException.class,
                code = {409})
        @UnexpectedResponseExceptionType(HttpResponseException.class)
        Mono<Response<BinaryData>> getCompletions(
                @HostParam("endpoint") String endpoint,
                @HeaderParam("accept") String accept,
                @BodyParam("application/json") BinaryData completionsOptions,
                RequestOptions requestOptions,
                Context context);

        @Post("/chat/completions")
        @ExpectedResponses({200})
        @UnexpectedResponseExceptionType(
                value = ClientAuthenticationException.class,
                code = {401})
        @UnexpectedResponseExceptionType(
                value = ResourceNotFoundException.class,
                code = {404})
        @UnexpectedResponseExceptionType(
                value = ResourceModifiedException.class,
                code = {409})
        @UnexpectedResponseExceptionType(HttpResponseException.class)
        Mono<Response<BinaryData>> getChatCompletions(
                @HostParam("endpoint") String endpoint,
                @HeaderParam("accept") String accept,
                @BodyParam("application/json") BinaryData chatCompletionsOptions,
                RequestOptions requestOptions,
                Context context);
    }
}
