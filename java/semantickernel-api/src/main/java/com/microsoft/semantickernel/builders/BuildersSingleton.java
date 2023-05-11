// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Enum singleton that service loads builder implementations */
public enum BuildersSingleton {
    INST;

    // Fallback classes in case the META-INF/services directory is missing
    private static final String FALLBACK_FUNCTION_BUILDER_CLASS =
            "com.microsoft.semantickernel.SkFunctionBuilders";
    private static final String FALLBACK_KERNEL_BUILDER_CLASS =
            "com.microsoft.semantickernel.KernelDefaultBuilder";
    private static final String FALLBACK_TEXT_COMPLETION_BUILDER_CLASS =
            "com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletionBuilder";

    private static final String FALLBACK_SKILL_COLLECTION_BUILDER_CLASS =
            "com.microsoft.semantickernel.skilldefinition.DefaultReadOnlySkillCollection.Builder";

    private static final String FALLBACK_PROMPT_TEMPLATE_BUILDER_CLASS =
            "com.microsoft.semantickernel.semanticfunctions.DefaultPromptTemplateBuilder";

    private final FunctionBuilders functionBuilders;
    private final Kernel.InternalBuilder kernelBuilder;
    private final TextCompletion.Builder textCompletionBuilder;
    private final ReadOnlySkillCollection.Builder readOnlySkillCollection;

    private final PromptTemplate.Builder promptTemplate;

    BuildersSingleton() {
        try {
            functionBuilders =
                    ServiceLoadUtil.findServiceLoader(
                            FunctionBuilders.class, FALLBACK_FUNCTION_BUILDER_CLASS);
            kernelBuilder =
                    ServiceLoadUtil.findServiceLoader(
                            Kernel.InternalBuilder.class, FALLBACK_KERNEL_BUILDER_CLASS);
            textCompletionBuilder =
                    ServiceLoadUtil.findServiceLoader(
                            TextCompletion.Builder.class, FALLBACK_TEXT_COMPLETION_BUILDER_CLASS);
            readOnlySkillCollection =
                    ServiceLoadUtil.findServiceLoader(
                            ReadOnlySkillCollection.Builder.class,
                            FALLBACK_SKILL_COLLECTION_BUILDER_CLASS);
            promptTemplate =
                    ServiceLoadUtil.findServiceLoader(
                            PromptTemplate.Builder.class, FALLBACK_PROMPT_TEMPLATE_BUILDER_CLASS);
        } catch (Throwable e) {
            Logger LOGGER = LoggerFactory.getLogger(BuildersSingleton.class);
            LOGGER.error("Failed to discover Semantic Kernel Builders", e);
            LOGGER.error(
                    "This is likely due to:\n\n"
                        + "- The Semantic Kernel implementation (typically provided by"
                        + " semantickernel-core) is not present on the classpath at runtime, ensure"
                        + " that this dependency is available at runtime. In maven this would be"
                        + " achieved by adding:\n"
                        + "\n"
                        + "        <dependency>\n"
                        + "            <groupId>com.microsoft.semantickernel</groupId>\n"
                        + "            <artifactId>semantickernel-core</artifactId>\n"
                        + "            <version>${skversion}</version>\n"
                        + "            <scope>runtime</scope>\n"
                        + "        </dependency>\n\n"
                        + "- The META-INF/services files that define the service loading have been"
                        + " filtered out and are not present within the running application\n\n"
                        + "- The class names have been changed (for instance shaded) preventing"
                        + " discovering the classes");

            throw e;
        }
    }

    public FunctionBuilders getFunctionBuilders() {
        return functionBuilders;
    }

    public Kernel.InternalBuilder getKernelBuilder() {
        return kernelBuilder;
    }

    public TextCompletion.Builder getTextCompletionBuilder() {
        return textCompletionBuilder;
    }

    public ReadOnlySkillCollection.Builder getReadOnlySkillCollection() {
        return readOnlySkillCollection;
    }

    public PromptTemplate.Builder getPromptTemplateBuilder() {
        return promptTemplate;
    }
}
