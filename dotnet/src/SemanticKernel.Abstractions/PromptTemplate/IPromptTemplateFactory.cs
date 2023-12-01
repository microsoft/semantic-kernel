// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Prompt template factory interface.
/// Implement this interface to provide support for a new prompt template format.
/// </summary>
public interface IPromptTemplateFactory
{
    /// <summary>
    /// Create an instance of <see cref="IPromptTemplate"/> from a template string and a configuration. Return null if the specified template format is not supported.
    /// </summary>
    /// <param name="promptConfig">Prompt template configuration</param>
    /// <returns>Instance of <see cref="IPromptTemplate"/></returns>
    /// <throws><see cref="KernelException"/> if template format is not supported</throws>
    IPromptTemplate Create(PromptTemplateConfig promptConfig);
}
