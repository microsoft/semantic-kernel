// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import java.util.Collections;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.function.Function;

import javax.annotation.Nullable;

public final class KernelConfig {

    private static final String DEFAULT_SERVICE_ID = "__SK_DEFAULT";
    private final Map<String, Function<Kernel, TextCompletion>> textCompletionServices;
    private final Map<String, Function<Kernel, ChatCompletion>> chatCompletionServices;

    private final Map<String, Function<Kernel, EmbeddingGeneration<String, Float>>>
            textEmbeddingGenerationServices;

    public KernelConfig(
            Map<String, Function<Kernel, TextCompletion>> textCompletionServices,
            Map<String, Function<Kernel, EmbeddingGeneration<String, Float>>>
                    textEmbeddingGenerationServices,
            Map<String, Function<Kernel, ChatCompletion>> chatCompletionServices) {
        this.textCompletionServices = new HashMap<>();
        this.textCompletionServices.putAll(textCompletionServices);
        this.textEmbeddingGenerationServices = new HashMap<>(textEmbeddingGenerationServices);
        this.chatCompletionServices = new HashMap<>(chatCompletionServices);
    }

    /**
     * Get the text completion services with the given id
     *
     * @param serviceId Service id
     * @return Map of text completion services
     */
    @Nullable
    public Function<Kernel, TextCompletion> getTextCompletionService(String serviceId) {
        return textCompletionServices.get(serviceId);
    }

    public Function<Kernel, TextCompletion> getTextCompletionServiceOrDefault(
            @Nullable String serviceId) {
        if (serviceId == null) {
            serviceId = DEFAULT_SERVICE_ID;
        }

        if (!this.textCompletionServices.containsKey(serviceId)) {
            throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "A text completion service id '"
                            + serviceId
                            + "' doesn't exist. This likely means a text completion service was not"
                            + " registered on this kernel.");
        }

        return this.textCompletionServices.get(serviceId);
    }

    public Function<Kernel, ChatCompletion> getChatCompletionServiceOrDefault(
            @Nullable String serviceId) {
        if (serviceId == null) {
            serviceId = DEFAULT_SERVICE_ID;
        }

        if (!this.chatCompletionServices.containsKey(serviceId)) {
            throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "A chat completion service id '" + serviceId + "' doesn't exist");
        }

        return this.chatCompletionServices.get(serviceId);
    }

    public Function<Kernel, EmbeddingGeneration<String, Float>>
            getTextEmbeddingGenerationServiceOrDefault(@Nullable String serviceId) {

        if (serviceId == null) {
            serviceId = DEFAULT_SERVICE_ID;
        }

        if (!this.textEmbeddingGenerationServices.containsKey(serviceId)) {
            throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "A embedding generation service id '" + serviceId + "' doesn't exist");
        }

        return this.textEmbeddingGenerationServices.get(serviceId);
    }

    public static class Builder {
        private Map<String, Function<Kernel, TextCompletion>> textCompletionServices =
                new HashMap<>();

        private Map<String, Function<Kernel, EmbeddingGeneration<String, Float>>>
                textEmbeddingGenerationServices = new HashMap<>();
        private final Map<String, Function<Kernel, ChatCompletion>> chatCompletionServices =
                new HashMap<>();

        // TODO, is there a need for this to be a factory?
        public Builder addTextCompletionService(
                String serviceId, Function<Kernel, TextCompletion> serviceFactory) {
            if (serviceId == null || serviceId.isEmpty()) {
                throw new IllegalArgumentException("Null or empty serviceId");
            }

            textCompletionServices.put(serviceId, serviceFactory);

            if (textCompletionServices.size() == 1) {
                textCompletionServices.put(DEFAULT_SERVICE_ID, serviceFactory);
            }
            return this;
        }

        public Builder addTextEmbeddingsGenerationService(
                String serviceId,
                Function<Kernel, EmbeddingGeneration<String, Float>> serviceFactory) {
            if (serviceId == null || serviceId.isEmpty()) {
                throw new IllegalArgumentException("Null or empty serviceId");
            }

            textEmbeddingGenerationServices.put(serviceId, serviceFactory);

            if (textEmbeddingGenerationServices.size() == 1) {
                textEmbeddingGenerationServices.put(DEFAULT_SERVICE_ID, serviceFactory);
            }
            return this;
        }

        public Builder setDefaultTextCompletionService(String serviceId) {
            if (!this.textCompletionServices.containsKey(serviceId)) {
                throw new KernelException(
                        KernelException.ErrorCodes.ServiceNotFound,
                        "A text completion service id '" + serviceId + "' doesn't exist");
            }

            this.textCompletionServices.put(
                    DEFAULT_SERVICE_ID, textCompletionServices.get(serviceId));

            return this;
        }

        /**
         * Add to the list a service for chat completion, e.g. OpenAI ChatGPT.
         *
         * @param serviceId Id used to identify the service
         * @param serviceFactory Function used to instantiate the service object
         * @return Current object instance
         */
        public Builder addChatCompletionService(
                @Nullable String serviceId, Function<Kernel, ChatCompletion> serviceFactory) {
            if (serviceId != null
                    && serviceId.toUpperCase(Locale.ROOT).equals(DEFAULT_SERVICE_ID)) {
                String msg =
                        "The service id '"
                                + serviceId
                                + "' is reserved, please use a different name";
                throw new KernelException(
                        KernelException.ErrorCodes.InvalidServiceConfiguration, msg);
            }

            if (serviceId == null) {
                serviceId = DEFAULT_SERVICE_ID;
            }

            this.chatCompletionServices.put(serviceId, serviceFactory);
            if (this.chatCompletionServices.size() == 1) {
                this.chatCompletionServices.put(DEFAULT_SERVICE_ID, serviceFactory);
            }

            return this;
        }

        public KernelConfig build() {
            return new KernelConfig(
                    Collections.unmodifiableMap(textCompletionServices),
                    textEmbeddingGenerationServices,
                    chatCompletionServices);
        }
    }
}
