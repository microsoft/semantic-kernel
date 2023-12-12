package com.microsoft.semantickernel.orchestration;

import javax.annotation.Nullable;

public class KernelFunctionYaml {

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown text.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction fromPromptYaml(
        String text,
        @Nullable PromptTemplateFactory promptTemplateFactory
    ) {
        return null;
    }

}
