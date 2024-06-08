// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides an implementation of <see cref="IPromptTemplateFactory"/> which creates no operation instances of <see cref="IPromptTemplate"/>.
/// </summary>
public sealed class NoopPromptTemplateFactory : IPromptTemplateFactory
{
    /// <inheritdoc/>
    public bool TryCreate(PromptTemplateConfig templateConfig, [NotNullWhen(true)] out IPromptTemplate? result)
    {
        result = new NoopPromptTemplate(templateConfig);

        return true;
    }
}
