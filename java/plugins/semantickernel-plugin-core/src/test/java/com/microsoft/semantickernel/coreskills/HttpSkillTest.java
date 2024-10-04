// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.azure.core.http.HttpClient;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.HttpResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

public class HttpSkillTest {

    private HttpSkill httpSkill;

    @Mock private HttpClient httpClient;

    @Mock private HttpResponse httpResponse;

    @BeforeEach
    public void setUp() {
        MockitoAnnotations.openMocks(this);
        httpSkill = new HttpSkill(httpClient);
    }

    @Test
    public void testGetAsync() {
        String url = "https://example.com";
        String responseBody = "Response body";
        when(httpResponse.getBodyAsString()).thenReturn(Mono.just(responseBody));
        when(httpClient.send(any(HttpRequest.class))).thenReturn(Mono.just(httpResponse));
        Mono<String> responseMono = httpSkill.getAsync(url);
        StepVerifier.create(responseMono).expectNext(responseBody).verifyComplete();
    }

    @Test
    public void testPostAsync() {
        String url = "https://example.com";
        String body = "{\"key\": \"value\"}";
        String responseBody = "Response body";
        when(httpResponse.getBodyAsString()).thenReturn(Mono.just(responseBody));
        when(httpClient.send(any(HttpRequest.class))).thenReturn(Mono.just(httpResponse));
        Mono<String> responseMono = httpSkill.postAsync(url, body);
        StepVerifier.create(responseMono).expectNext(responseBody).verifyComplete();
    }

    @Test
    public void testPutAsync() {
        String url = "https://example.com";
        String body = "{\"key\": \"value\"}";
        String responseBody = "Response body";
        when(httpResponse.getBodyAsString()).thenReturn(Mono.just(responseBody));
        when(httpClient.send(any(HttpRequest.class))).thenReturn(Mono.just(httpResponse));
        Mono<String> responseMono = httpSkill.putAsync(url, body);
        StepVerifier.create(responseMono).expectNext(responseBody).verifyComplete();
    }

    @Test
    public void testDeleteAsync() {
        String url = "https://example.com";
        when(httpClient.send(any(HttpRequest.class))).thenReturn(Mono.just(httpResponse));
        Mono<HttpResponse> responseMono = httpSkill.deleteAsync(url);
        StepVerifier.create(responseMono).expectNext(httpResponse).verifyComplete();
    }
}
