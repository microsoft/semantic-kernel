// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a <see cref="IPromptTemplateFactory"/> which aggregates multiple prompt template factories.
/// </summary>
/// <remarks>
/// Attempts via <see cref="TryCreate"/> to create an <see cref="IPromptTemplate"/> from a
/// <see cref="PromptTemplateConfig"/> will iterate through the aggregated factories, using
/// the result from the first to successfully handle the supplied configuration.
/// </remarks>
public sealed class AggregatorPromptTemplateFactory : IPromptTemplateFactory
{
    private readonly IPromptTemplateFactory?[] _promptTemplateFactories;

    /// <summary>Initializes the instance.</summary>
    /// <param name="promptTemplateFactories">Ordered <see cref="IPromptTemplateFactory"/> instances to aggregate.</param>
    public AggregatorPromptTemplateFactory(params IPromptTemplateFactory[] promptTemplateFactories)
    {
        Verify.NotNullOrEmpty(promptTemplateFactories);
        foreach (IPromptTemplateFactory promptTemplateFactory in promptTemplateFactories)
        {
            Verify.NotNull(promptTemplateFactory, nameof(promptTemplateFactories));
        }

        this._promptTemplateFactories = promptTemplateFactories;
    }

    /// <inheritdoc/>
    public bool TryCreate(PromptTemplateConfig templateConfig, [NotNullWhen(true)] out IPromptTemplate? result)
    {
        Verify.NotNull(templateConfig);

        foreach (var promptTemplateFactory in this._promptTemplateFactories)
        {
            if (promptTemplateFactory?.TryCreate(templateConfig, out result) is true && result is not null)
            {
                return true;
            }
        }

        result = null;
        return false;
    }
}
