// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Prompt template factory interface.
/// Implement this interface to provide support for a new prompt template format.
/// </summary>
public interface IPromptTemplateFactory
{
    /// <summary>
    /// Create an instance of <see cref="IPromptTemplate"/> from a template string and a configuration.
    /// </summary>
    /// <param name="templateString">Template string using the format associated with this <see cref="IPromptTemplateFactory"/></param>
    /// <param name="promptTemplateConfig">Prompt template configuration</param>
    /// <returns></returns>
    IPromptTemplate CreatePromptTemplate(string templateString, PromptTemplateConfig promptTemplateConfig);
}
