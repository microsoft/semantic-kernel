package com.microsoft.semantickernel.plugins.web.bing;

import java.util.List;

import com.azure.core.http.HttpClient;

import reactor.core.publisher.Mono;

public class BingConnector {    

    public BingConnector(String apiKey, HttpClient httpClient) {
    }

    public Mono<List<String>> searchAsync(String query, int count, int offset) {
        return Mono.error(() -> new UnsupportedOperationException("Not implemented yet"));
    }

}
