// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Represents a type used to manage the instantiation of <see cref = "IPromptTemplateEngine" />s.
/// </summary>
public interface IPromptTemplateEngineFactory
{
    /// <summary>
    /// Creates a new <see cref = "IPromptTemplateEngine" /> for the specified format for use with the specified kernel and context.
    ///
    /// This should be called when a template is being rendered so it will need to be extended to include SKContext as a parameter.
    /// </summary>
    /// <param name="format"></param>
    /// <param name="loggerFactory"></param>
    /// <returns>Instance of <see cref = "IPromptTemplateEngine" /></returns>
    IPromptTemplateEngine Create(string format, ILoggerFactory? loggerFactory = null);
}
