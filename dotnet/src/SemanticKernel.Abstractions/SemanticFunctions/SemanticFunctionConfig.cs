// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.SemanticFunctions;

/// <summary>
/// Semantic function configuration.
/// </summary>
public sealed class SemanticFunctionConfig
{
    /// <summary>
    /// Prompt template configuration.
    /// </summary>
    public PromptTemplateConfig PromptTemplateConfig { get; }

    /// <summary>
    /// Prompt template.
    /// </summary>
    public IPromptTemplate PromptTemplate { get; }

    /// <summary>
    /// Constructor for SemanticFunctionConfig.
    /// </summary>
    /// <param name="config">Prompt template configuration.</param>
    /// <param name="template">Prompt template.</param>
    public SemanticFunctionConfig(
        PromptTemplateConfig config,
        IPromptTemplate template)
    {
        this.PromptTemplateConfig = config;
        this.PromptTemplate = template;
    }
}
