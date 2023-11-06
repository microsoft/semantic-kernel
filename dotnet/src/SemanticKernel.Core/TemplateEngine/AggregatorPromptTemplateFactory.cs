// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Implementation of <see cref="IPromptTemplateFactory"/> which aggregates multiple prompt template factories.
/// </summary>
public class AggregatorPromptTemplateFactory : IPromptTemplateFactory
{
    private readonly IPromptTemplateFactory[] _promptTemplateFactories;

    /// <summary>
    /// Constructor for <see cref="AggregatorPromptTemplateFactory"/>.
    /// </summary>
    /// <param name="promptTemplateFactories">List of <see cref="IPromptTemplateFactory"/> instances</param>
    public AggregatorPromptTemplateFactory(params IPromptTemplateFactory[] promptTemplateFactories)
    {
        Verify.NotNull(promptTemplateFactories);

        if (promptTemplateFactories.Length == 0)
        {
            throw new SKException("At least one prompt template factory must be specified.");
        }

        this._promptTemplateFactories = promptTemplateFactories;
    }

    /// <summary>
    /// Create an instance of <see cref="IPromptTemplate"/> from a template string and a configuration. Throws an <see cref="SKException"/> if the specified template format is not supported.
    /// </summary>
    /// <param name="templateString">Template string using the format associated with this <see cref="IPromptTemplateFactory"/></param>
    /// <param name="promptTemplateConfig">Prompt template configuration</param>
    /// <returns></returns>
    public IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig)
    {
        foreach (var promptTemplateFactory in this._promptTemplateFactories)
        {
            try
            {
                var promptTemplate = promptTemplateFactory.Create(templateString, promptTemplateConfig);
                if (promptTemplate != null)
                {
                    return promptTemplate;
                }
            }
            catch (SKException)
            {
                // Ignore the exception and try the next factory
            }
        }

        throw new SKException($"Prompt template format {promptTemplateConfig.TemplateFormat} is not supported.");
    }
}
