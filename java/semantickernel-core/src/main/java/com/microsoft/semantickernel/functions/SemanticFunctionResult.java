// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.functions;

import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunction;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

public class SemanticFunctionResult implements FunctionResult {
    private Mono<String> valueAsync;
    private Flux<String> streamingValueAsync;
    private boolean isStreaming;
    private String functionName;
    private String pluginName;
    private Map<String, Object> metadata;

    public SemanticFunctionResult() {}

    public SemanticFunctionResult(String pluginName, String functionName, Mono<String> valueAsync) {
        this.valueAsync = valueAsync;
        this.pluginName = pluginName;
        this.functionName = functionName;
        this.isStreaming = false;
    }

    public SemanticFunctionResult(String pluginName, String functionName, Mono<String> valueAsync, Flux<String> streamingValueAsync) {
        this.pluginName = pluginName;
        this.functionName = functionName;
        this.valueAsync = valueAsync;
        this.isStreaming = true;
        this.streamingValueAsync = streamingValueAsync;
    }

    @Override
    public String functionName() {
        return null;
    }

    @Override
    public String pluginName() {
        return null;
    }

    @Override
    public Map<String, Object> metadata() {
        return null;
    }

    @Override
    public Flux<String> getStreamingValueAsync() {
        return streamingValueAsync;
    }

    @Override
    public Mono<String> getValueAsync() {
        return valueAsync;
    }

    @Override
    public String getValue() {
        return valueAsync.block();
    }

    @Override
    public <T> T tryGetMetadataValue(String key) {
        return null;
    }
}
