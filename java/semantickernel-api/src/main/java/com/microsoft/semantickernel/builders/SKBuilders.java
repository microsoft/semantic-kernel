// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

public class SKBuilders {
    // Prevent creating object
    private SKBuilders() {}

    public static CompletionSKFunction.Builder completionFunctions() {
        return FunctionBuilders.getCompletionBuilder();
    }

    public static TextCompletion.Builder textCompletionService() {
        return BuildersSingleton.INST.getTextCompletionBuilder();
    }

    public static EmbeddingGeneration.Builder<String, Float> textEmbeddingGenerationService() {
        return BuildersSingleton.INST.getTextEmbeddingGenerationBuilder();
    }

    public static Kernel.Builder kernel() {
        return new Kernel.Builder();
    }

    public static KernelConfig.Builder kernelConfig() {
        return new KernelConfig.Builder();
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
}
