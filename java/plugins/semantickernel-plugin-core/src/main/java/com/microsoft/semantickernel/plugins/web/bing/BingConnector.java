package com.microsoft.semantickernel.plugins.web.bing;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import com.azure.core.http.HttpClient;
import com.azure.core.http.HttpHeader;
import com.azure.core.http.HttpHeaderName;
import com.azure.core.http.HttpHeaders;
import com.azure.core.http.HttpMethod;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.HttpResponse;
import com.azure.core.implementation.jackson.ObjectMapperShim;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationConfig;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;

import reactor.core.publisher.Mono;

public class BingConnector {    

    private static String BING_SEARCH_URL;
    static { 
        String bingSearchUrl = System.getProperty("bing.search.url"); 
        if (bingSearchUrl == null || bingSearchUrl.isEmpty()) bingSearchUrl = System.getenv("BING_SEARCH_URL");
        if (bingSearchUrl == null || bingSearchUrl.isEmpty()) bingSearchUrl = "https://api.bing.microsoft.com/v7.0/search";
        BING_SEARCH_URL = bingSearchUrl;
    }

    private static final String OCP_APIM_SUBSCRIPTION_KEY = "Ocp-Apim-Subscription-Key";
    private static final HttpHeaderName OCP_APIM_SUBSCRIPTION_KEY_HEADER = HttpHeaderName.fromString(OCP_APIM_SUBSCRIPTION_KEY);

    private static class BingSearchResponse {
        private final WebPages webPages;
        @JsonCreator
        public BingSearchResponse(
            @JsonProperty("webPages") WebPages webPages
        ) {
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
            @JsonProperty("value") WebPage[] value
        ) {
            this.value = value;
        }

        public WebPage[] getValue() {
            return value;
        }
    }

    public static class WebPage {
        @JsonProperty("name")
        private String name;

        @JsonProperty("url")
        private String url;

        @JsonProperty("snippet")
        private String snippet;

        public WebPage() {
        }

        public String getName() {
            return name;
        }

        public String getUrl() {
            return url;
        }

        public String getSnippet() {
            return snippet;
        }   

        public void setName(String name) {
            this.name = name;
        }

        public void setUrl(String url) {
            this.url = url;
        }

        public void setSnippet(String snippet) {
            this.snippet = snippet;
        }   
    }

    private final String apiKey; // TODO: secure this
    private final HttpClient httpClient;
    public BingConnector(String apiKey, HttpClient httpClient) {
        this.apiKey = apiKey;
        this.httpClient = httpClient;
    }

    public Mono<List<String>> searchAsync(String query, int count, int offset) {   

        if (count <= 0 || 50 <= count) throw new IllegalArgumentException("count must be between 1 and 50");
        if (offset < 0) throw new IllegalArgumentException("offset must be greater than or equal to 0");

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

    private static Mono<List<String>> handleResponse(HttpResponse response) {
            return response.getBodyAsString()
                .flatMap(body -> {
                    if (body == null || body.isEmpty()) return Mono.empty();
                    try {
                        ObjectMapper objectMapper = new ObjectMapper()
                            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
                            .configure(DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES, false);
                        BingSearchResponse bingSearchResponse = objectMapper.readValue(body, BingSearchResponse.class);
                        List<String> urls = new ArrayList<String>();
                        for (WebPage webPage : bingSearchResponse.getWebPages().getValue()) {
                            urls.add(webPage.getUrl());
                        }
                        return Mono.just(urls);
                    } catch (JsonProcessingException e) {
                        Mono.error(e);
                    }
                    return Mono.empty();
                });
    }
}
