// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.guice;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.google.inject.AbstractModule;
import com.google.inject.TypeLiteral;
import com.google.inject.util.Providers;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion;
import com.microsoft.semantickernel.connectors.ai.openai.textembeddings.OpenAITextEmbeddingGeneration;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.DefaultSkillCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;

import javax.annotation.Nullable;

public class SemanticKernelModule extends AbstractModule {

    private final SemanticTextMemory memory;
    private final KernelConfig.Builder kernelConfig;
    private final ReadOnlySkillCollection skillCollection;
    private final PromptTemplateEngine promptTemplateEngine;
    private String textCompletionModelId;
    private boolean withMemory;
    private String embeddingsGenerationServiceId;
    private OpenAIAsyncClient client;

    public SemanticKernelModule(
            KernelConfig.Builder kernelConfig,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skillCollection,
            @Nullable PromptTemplateEngine promptTemplateEngine) {
        this.kernelConfig = kernelConfig;

        if (memory != null) {
            this.memory = memory.copy();
        } else {
            this.memory = null;
        }

        if (skillCollection == null) {
            skillCollection = new DefaultSkillCollection();
        }
        this.skillCollection = skillCollection;

        if (promptTemplateEngine == null) {
            promptTemplateEngine = new DefaultPromptTemplateEngine();
        }
        this.promptTemplateEngine = promptTemplateEngine;
    }

    public SemanticKernelModule(
            KernelConfig.Builder kernelConfig, @Nullable SemanticTextMemory memory) {
        this(kernelConfig, memory, null, null);
    }

    public SemanticKernelModule(KernelConfig.Builder kernelConfig) {
        this(kernelConfig, null);
    }

    public SemanticKernelModule() {
        this(SKBuilders.kernelConfig(), null);
    }

    public SemanticKernelModule withTextCompletionService(String model) {
        this.textCompletionModelId = model;
        return this;
    }

    public SemanticKernelModule withClient(OpenAIAsyncClient client) {
        this.client = client;
        return this;
    }

    @Override
    protected void configure() {
        super.configure();

        if (client == null) {
            client = Config.getClient(true);
        }

        bind(OpenAIAsyncClient.class).toInstance(client);

        if (embeddingsGenerationServiceId != null) {
            OpenAITextEmbeddingGeneration embeddings = new OpenAITextEmbeddingGeneration(client,
                    embeddingsGenerationServiceId);
            bind(new TypeLiteral<EmbeddingGeneration<String>>() {
            }).toInstance(embeddings);
        }


        bind(KernelConfig.class).toInstance(kernelConfig.build());
        bind(PromptTemplateEngine.class).toInstance(promptTemplateEngine);
        bind(ReadOnlySkillCollection.class).toProvider(Providers.of(skillCollection));

        if (withMemory) {
            bind(SemanticTextMemory.class).toProvider(Providers.of(memory));
        } else {
            bind(SemanticTextMemory.class).toInstance(NullMemory.getInstance());
        }

        bind(Kernel.class).toProvider(() -> {
            Kernel.Builder builder = SKBuilders.kernel();
            if (textCompletionModelId != null) {
                builder.withDefaultAIService(new OpenAITextCompletion(client, textCompletionModelId));
            }
            return builder.build();
        });

        bind(CompletionFunctionFactory.class)
                .to(CompletionFunctionFactory.CompletionFunctionFactoryImpl.class);
    }

    public SemanticKernelModule withMemory() {
        this.withMemory = true;
        return this;
    }

    public SemanticKernelModule withTextEmbeddingsGenerationService(
            String embeddingsGenerationServiceId) {
        this.embeddingsGenerationServiceId = embeddingsGenerationServiceId;
        return this;
    }
}
