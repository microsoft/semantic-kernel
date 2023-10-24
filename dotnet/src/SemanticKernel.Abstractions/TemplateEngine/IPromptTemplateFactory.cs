// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// TODO Mark
/// </summary>
public interface IPromptTemplateFactory
{
    /// <summary>
    /// TODO Mark
    /// </summary>
    /// <param name="templateString"></param>
    /// <param name="promptTemplateConfig"></param>
    /// <returns></returns>
    IPromptTemplate? CreatePromptTemplate(string templateString, PromptTemplateConfig promptTemplateConfig);
}
