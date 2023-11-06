// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.guice;

import com.google.inject.Guice;
import com.google.inject.Injector;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;

import jakarta.inject.Inject;

import java.util.ArrayList;
import java.util.List;

public class GuiceEmbeddingExample {

    private final EmbeddingGeneration<String> embeddingGeneration;

    public static void main(String[] args) {
        Injector injector =
                Guice.createInjector(
                        new SemanticKernelModule()
                                .withMemory()
                                .withTextEmbeddingsGenerationService("text-embedding-ada-002"));

        GuiceEmbeddingExample example = injector.getInstance(GuiceEmbeddingExample.class);
        example.run();
    }

    @Inject
    public GuiceEmbeddingExample(EmbeddingGeneration<String> embeddingGeneration) {
        this.embeddingGeneration = embeddingGeneration;
    }

    public void run() {
        List<String> data = new ArrayList<>();
        data.add("This is just a test");

        embeddingGeneration
                .generateEmbeddingsAsync(data)
                .block()
                .forEach(
                        doubleEmbedding -> {
                            doubleEmbedding.getVector().forEach(System.out::println);
                        });
    }
}
