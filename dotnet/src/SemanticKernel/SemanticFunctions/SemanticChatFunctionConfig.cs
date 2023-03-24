// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.SemanticFunctions;

/// <summary>
/// Semantic function configuration.
/// </summary>
public sealed class SemanticChatFunctionConfig
{
    /// <summary>
    /// Prompt template configuration.
    /// </summary>
    public ChatPromptTemplateConfig PromptTemplateConfig { get; }

    /// <summary>
    /// Prompt template.
    /// </summary>
    public IChatPromptTemplate PromptTemplate { get; }

    /// <summary>
    /// Constructor for SemanticFunctionConfig.
    /// </summary>
    /// <param name="config">Prompt template configuration.</param>
    /// <param name="template">Prompt template.</param>
    public SemanticChatFunctionConfig(ChatPromptTemplateConfig config, IChatPromptTemplate template)
    {
        this.PromptTemplateConfig = config;
        this.PromptTemplate = template;
    }
}
