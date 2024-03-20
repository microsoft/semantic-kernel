// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.connectors.web.bing;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;

import com.azure.core.http.HttpClient;
import com.azure.core.http.HttpHeaderName;
import com.azure.core.http.HttpMethod;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.HttpResponse;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.connectors.WebSearchEngineConnector;
import com.microsoft.semantickernel.exceptions.SKException;

import reactor.core.publisher.Mono;

public class BingConnector implements WebSearchEngineConnector {

    private static String BING_SEARCH_URL;
static {
        String bingSearchUrl = System.getProperty("bing.search.url");
        if (bingSearchUrl == null || bingSearchUrl.isEmpty())
            bingSearchUrl = System.getenv("BING_SEARCH_URL");
        if (bingSearchUrl == null || bingSearchUrl.isEmpty())
            bingSearchUrl = "https://api.bing.microsoft.com/v7.0/search";
        BING_SEARCH_URL = bingSearchUrl;
    }

    private static final String OCP_APIM_SUBSCRIPTION_KEY = "Ocp-Apim-Subscription-Key";
    private static final HttpHeaderName OCP_APIM_SUBSCRIPTION_KEY_HEADER = HttpHeaderName
        .fromString(OCP_APIM_SUBSCRIPTION_KEY);

    private static class BingSearchResponse {
        private final WebPages webPages;

        @JsonCreator
        public BingSearchResponse(
            @JsonProperty("webPages") WebPages webPages) {
            this.webPages = webPages;
        }

        public WebPages getWebPages() {
            return webPages;
        }
    }

    private static class WebPages {
        private final WebPage[] value;

        @JsonCreator
        public WebPages(
            @JsonProperty("value") BingWebPage[] value) {
            this.value = value;
        }

        public WebPage[] getValue() {
            return value;
        }
    }

    public static class BingWebPage implements WebPage {
        private final String name;
        private final String url;
        private final String snippet;

        @JsonCreator
        public BingWebPage(
            @JsonProperty("name") String name,
            @JsonProperty("url") String url,
            @JsonProperty("snippet") String snippet) {
            this.name = name;
            this.url = url;
            this.snippet = snippet;
        }

        @Override
        public String getName() {
            return name;
        }

        @Override
        public String getUrl() {
            return url;
        }

        @Override
        public String getSnippet() {
            return snippet;
        }
    }

    private final String apiKey; // TODO: secure this
    private final HttpClient httpClient;

    public BingConnector(String apiKey, HttpClient httpClient) {
        this.apiKey = apiKey;
        this.httpClient = httpClient;
    }

    public BingConnector(String apiKey) {
        this(apiKey, HttpClient.createDefault());
    }

    @Override
    public Mono<List<WebPage>> searchAsync(String query, int count, int offset) {

        if (count <= 0 || 50 <= count)
            throw new IllegalArgumentException("count must be between 1 and 50");
        if (offset < 0)
            throw new IllegalArgumentException("offset must be greater than or equal to 0");

        HttpRequest request = new HttpRequest(HttpMethod.GET, searchUrl(query, count, offset));
        request.setHeader(OCP_APIM_SUBSCRIPTION_KEY_HEADER, apiKey);

        return httpClient.send(request).flatMap(BingConnector::handleResponse);

    }

    private static String searchUrl(String query, int count, int offset) {

        try {
            query = URLEncoder.encode(query, StandardCharsets.UTF_8.toString());
        } catch (UnsupportedEncodingException e) {
            // ignored - UTF-8 is always supported
        }

        String url = String.format("%s?q=%s&count=%s&offset=%s",
            BING_SEARCH_URL, query, Integer.toString(count), Integer.toString(offset));
        return url;
    }

    private static Mono<List<WebPage>> handleResponse(HttpResponse response) {
        return response.getBodyAsString()
            .map(body -> {
                if (body == null || body.isEmpty())
                    return null;
                try {
                    ObjectMapper objectMapper = new ObjectMapper()
                        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
                        .configure(DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES,
                            false);

                    BingSearchResponse bingSearchResponse = objectMapper.readValue(body,
                        BingSearchResponse.class);
                    if (bingSearchResponse.getWebPages() != null
                        && bingSearchResponse.getWebPages().getValue() != null) {
                        return Arrays.asList(bingSearchResponse.getWebPages().getValue());
                    }
                } catch (JsonProcessingException e) {
                    throw new SKException(e.getMessage(), e);
                }
                return null;
            });
    }
}
