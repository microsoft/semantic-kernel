// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import javax.annotation.Nullable;

/**
 * The interface that a {@code PromptTemplateFactory} implementation must provide.
 */
public interface PromptTemplateFactory {

    /**
     * Create a prompt template, if possible, from the given configuration. This is a convenience
     * method that wraps the {@link KernelPromptTemplateFactory#tryCreate(PromptTemplateConfig)}
     * method.
     *
     * @param templateConfig The configuration for the prompt template.
     * @return The prompt template.
     * @throws UnknownTemplateFormatException If the template format is not supported.
     * @see PromptTemplateConfig#getTemplateFormat()
     */
    static PromptTemplate build(PromptTemplateConfig templateConfig) {
        return new KernelPromptTemplateFactory().tryCreate(templateConfig);
    }

    /**
     * Create a prompt template, if possible, from the given configuration. If the
     * {@code PromptTemplateConfig} is not supported, the method should throw an
     * {@code UnknownTemplateFormatException}.
     *
     * @param templateConfig The configuration for the prompt template.
     * @return The prompt template.
     * @throws UnknownTemplateFormatException If the template format is not supported.
     * @see PromptTemplateConfig#getTemplateFormat()
     */
    PromptTemplate tryCreate(PromptTemplateConfig templateConfig);

    /**
     * Exception thrown when the template format is not supported.
     *
     * @see PromptTemplateConfig#getTemplateFormat()
     */
    class UnknownTemplateFormatException extends IllegalArgumentException {

        /**
         * Constructor.
         *
         * @param templateFormat The template format that is not supported.
         */
        public UnknownTemplateFormatException(@Nullable String templateFormat) {
            super("Unknown template format: " + templateFormat);
        }
    }
}
