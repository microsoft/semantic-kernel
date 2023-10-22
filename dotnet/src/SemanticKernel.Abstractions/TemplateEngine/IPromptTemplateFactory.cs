// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// TODO
/// </summary>
public interface IPromptTemplateFactory
{
    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="templateFormat"></param>
    /// <param name="templateString"></param>
    /// <returns></returns>
    IPromptTemplate CreatePromptTemplate(string templateFormat, string templateString);
}
