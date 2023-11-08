// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Prompt template factory interface.
/// Implement this interface to provide support for a new prompt template format.
/// </summary>
public interface IPromptTemplateFactory
{
    /// <summary>
    /// Create an instance of <see cref="IPromptTemplate"/> from a template string and a configuration. Return null if the specified template format is not supported.
    /// </summary>
    /// <param name="templateString">Template string using the format associated with this <see cref="IPromptTemplateFactory"/></param>
    /// <param name="promptTemplateConfig">Prompt template configuration</param>
    /// <returns>Instance of <see cref="IPromptTemplate"/></returns>
    /// <throws><see cref="SKException"/> if template format is not supported</throws>
    IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig);
}
