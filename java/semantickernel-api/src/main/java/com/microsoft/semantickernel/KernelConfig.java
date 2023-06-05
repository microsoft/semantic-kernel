// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import java.util.*;
import java.util.function.Function;

import javax.annotation.Nullable;

public final class KernelConfig {

    private static final String DEFAULT_SERVICE_ID = "__SK_DEFAULT";
    private final Map<String, Function<Kernel, TextCompletion>> textCompletionServices;

    private final Map<String, Function<Kernel, EmbeddingGeneration<String, Float>>>
            textEmbeddingGenerationServices;
    private final ArrayList<SKFunction<?, ?>> skills;

    public KernelConfig(
            Map<String, Function<Kernel, TextCompletion>> textCompletionServices,
            Map<String, Function<Kernel, EmbeddingGeneration<String, Float>>>
                    textEmbeddingGenerationServices,
            List<SKFunction<?, ?>> skills) {
        this.textCompletionServices = new HashMap<>();
        this.textCompletionServices.putAll(textCompletionServices);
        this.textEmbeddingGenerationServices = new HashMap<>(textEmbeddingGenerationServices);
        this.skills = new ArrayList<>(skills);
    }

    @Nullable
    public Function<Kernel, TextCompletion> getTextCompletionService(String serviceId) {
        return textCompletionServices.get(serviceId);
    }

    public List<SKFunction<?, ?>> getSkills() {
        return Collections.unmodifiableList(skills);
    }

    public Function<Kernel, TextCompletion> getTextCompletionServiceOrDefault(
            @Nullable String serviceId) {
        if (serviceId == null) {
            serviceId = DEFAULT_SERVICE_ID;
        }

        if (!this.textCompletionServices.containsKey(serviceId)) {
            throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "A text completion service id '" + serviceId + "' doesn't exist");
        }

        return this.textCompletionServices.get(serviceId);
    }

    public static class Builder {
        private Map<String, Function<Kernel, TextCompletion>> textCompletionServices =
                new HashMap<>();

        private List<SKFunction<?, ?>> skillBuilders = new ArrayList<>();

        private Map<String, Function<Kernel, EmbeddingGeneration<String, Float>>>
                textEmbeddingGenerationServices = new HashMap<>();

        public Builder addSkill(SKFunction<?, ?> functionDefinition) {
            skillBuilders.add(functionDefinition);
            return this;
        }

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

        public KernelConfig build() {
            return new KernelConfig(
                    Collections.unmodifiableMap(textCompletionServices),
                    textEmbeddingGenerationServices,
                    skillBuilders);
        }
    }
}
