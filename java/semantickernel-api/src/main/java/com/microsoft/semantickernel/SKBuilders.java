// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

public class SKBuilders {
    // Prevent creating object
    private SKBuilders() {}

    public static TextCompletion.Builder textCompletionService() {
        return BuildersSingleton.INST.getInstance(TextCompletion.Builder.class);
    }

    public static EmbeddingGeneration.Builder<String> textEmbeddingGenerationService() {
        return BuildersSingleton.INST.getTextEmbeddingGenerationBuilder();
    }

    public static Kernel.Builder kernel() {
        return BuildersSingleton.INST.getInstance(Kernel.Builder.class);
    }

    public static KernelConfig.Builder kernelConfig() {
        return new KernelConfig.Builder();
    }

    public static SemanticTextMemory.Builder semanticTextMemory() {
        return BuildersSingleton.INST.getSemanticTextMemoryBuilder();
    }

    public static ReadOnlySkillCollection.Builder skillCollection() {
        return BuildersSingleton.INST.getReadOnlySkillCollection();
    }

    public static PromptTemplate.Builder promptTemplate() {
        return BuildersSingleton.INST.getPromptTemplateBuilder();
    }

    public static PromptTemplateEngine.Builder promptTemplateEngine() {
        return BuildersSingleton.INST.getPromptTemplateEngineBuilder();
    }

    public static ContextVariables.Builder variables() {
        return BuildersSingleton.INST.variables();
    }

    public static SKContext.Builder context() {
        return BuildersSingleton.INST.context();
    }

    public static PromptTemplateConfig.CompletionConfigBuilder completionConfig() {
        return new PromptTemplateConfig.CompletionConfigBuilder();
    }

    public static ChatCompletion.Builder chatCompletion() {
        return BuildersSingleton.INST.getChatCompletion();
    }

    public static MemoryStore.Builder memoryStore() {
        return BuildersSingleton.INST.getMemoryStoreBuilder();
    }

    public static CompletionSKFunction.Builder completionFunctions() {
        return BuildersSingleton.INST.getInstance(CompletionSKFunction.Builder.class);
    }
}
