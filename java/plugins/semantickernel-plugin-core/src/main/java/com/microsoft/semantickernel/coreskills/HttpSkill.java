// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.azure.core.http.HttpClient;
import com.azure.core.http.HttpMethod;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.HttpResponse;
import reactor.core.publisher.Mono;

/**
 * A skill that provides HTTP functionality.
 *
 * <p>Usage:
 *
 * <p>Usage: kernel.importSkill(new HttpSkill(), "http");
 *
 * <p>Examples:
 *
 * <p>{{http.getAsync $url}}
 *
 * <p>{{http.postAsync $url}}
 *
 * <p>{{http.putAsync $url}}
 *
 * <p>{{http.deleteAsync $url}}
 */
public class HttpSkill {

    private final HttpClient httpClient;

    public HttpSkill() {
        this.httpClient = HttpClient.createDefault();
    }

    public HttpSkill(HttpClient httpClient) {
        this.httpClient = httpClient;
    }

    /**
     * Sends an HTTP GET request to the specified URI and returns body as a string.
     *
     * @param url The URI to send the request to.
     * @return The response body as a string.
     */
    public Mono<String> getAsync(String url) {
        if (url == null || url.isEmpty()) {
            return Mono.error(new IllegalArgumentException("url cannot be `null` or empty"));
        }
        HttpRequest request = new HttpRequest(HttpMethod.GET, url);
        return httpClient.send(request).flatMap(response -> response.getBodyAsString());
    }

    /**
     * Sends an HTTP POST request to the specified URI and returns body as a string.
     *
     * @param url The URI to send the request to.
     * @param body The response body as a string.
     * @return
     */
    public Mono<String> postAsync(String url, String body) {
        if (url == null || url.isEmpty()) {
            return Mono.error(new IllegalArgumentException("url cannot be `null` or empty"));
        }
        HttpRequest request = new HttpRequest(HttpMethod.POST, url);
        request.setBody(body);
        return httpClient.send(request).flatMap(response -> response.getBodyAsString());
    }

    /**
     * Sends an HTTP PUT request to the specified URI and returns body as a string.
     *
     * @param url The URI to send the request to.
     * @param body The response body as a string.
     * @return
     */
    public Mono<String> putAsync(String url, String body) {
        if (url == null || url.isEmpty()) {
            return Mono.error(new IllegalArgumentException("url cannot be `null` or empty"));
        }
        HttpRequest request = new HttpRequest(HttpMethod.PUT, url);
        request.setBody(body);
        return httpClient.send(request).flatMap(response -> response.getBodyAsString());
    }

    /**
     * Sends an HTTP DELETE request to the specified URI and returns body as a string.
     *
     * @param url The URI to send the request to.
     * @return The response body as a string.
     */
    public Mono<HttpResponse> deleteAsync(String url) {
        if (url == null || url.isEmpty()) {
            return Mono.error(new IllegalArgumentException("url cannot be `null` or empty"));
        }
        HttpRequest request = new HttpRequest(HttpMethod.DELETE, url);
        return httpClient.send(request).flatMap(response -> Mono.just(response));
    }
}
