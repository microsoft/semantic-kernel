// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure

namespace Microsoft.SemanticKernel;

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
            throw new KernelException("At least one prompt template factory must be specified.");
        }

        this._promptTemplateFactories = promptTemplateFactories;
    }

    /// <summary>
    /// Create an instance of <see cref="IPromptTemplate"/> from a template string and a configuration. Throws an <see cref="KernelException"/> if the specified template format is not supported.
    /// </summary>
    /// <param name="promptConfig">Prompt template configuration</param>
    /// <returns></returns>
    public IPromptTemplate Create(PromptTemplateConfig promptConfig)
    {
        foreach (var promptTemplateFactory in this._promptTemplateFactories)
        {
            try
            {
                var promptTemplate = promptTemplateFactory.Create(promptConfig);
                if (promptTemplate != null)
                {
                    return promptTemplate;
                }
            }
            catch (KernelException)
            {
                // Ignore the exception and try the next factory
            }
        }

        throw new KernelException($"Prompt template format {promptConfig.TemplateFormat} is not supported.");
    }
}
