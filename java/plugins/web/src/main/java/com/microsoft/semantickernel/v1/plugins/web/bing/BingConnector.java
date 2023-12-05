package com.microsoft.semantickernel.plugins.web.bing;

import java.util.Collection;
import java.util.List;

import com.azure.core.http.HttpClient;

import reactor.core.publisher.Mono;

public class BingConnector {    

    public BingConnector(String apiKey, HttpClient httpClient) {
    }

    public Mono<Collection<String>> searchAsync(String query, int count, int offset) {
        return Mono.just(List.of());
    }

}
