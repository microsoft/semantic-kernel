// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a factory for prompt templates for one or more prompt template formats.
/// </summary>
public interface IPromptTemplateFactory
{
    /// <summary>
    /// Creates an instance of <see cref="IPromptTemplate"/> from a <see cref="PromptTemplateConfig"/>.
    /// </summary>
    /// <param name="templateConfig">Prompt template configuration</param>
    /// <param name="result">The created template, or null if the specified template format is not supported.</param>
    /// <returns>true if the format is supported and the template can be created; otherwise, false.</returns>
    bool TryCreate(PromptTemplateConfig templateConfig, [NotNullWhen(true)] out IPromptTemplate? result);
}
