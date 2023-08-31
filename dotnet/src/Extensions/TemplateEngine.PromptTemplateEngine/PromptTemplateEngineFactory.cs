// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.TemplateEngine.Prompt;

/// <summary>
/// Default implementation of <see cref = "IPromptTemplateEngine" /> which will be used with instances
/// of <see cref = "IKernel" /> if no alternate implementation is provided.
/// </summary>
public class PromptTemplateEngineFactory : IPromptTemplateEngineFactory
{
    /// <inheritdoc/>
    public IPromptTemplateEngine Create(string format, ILoggerFactory? loggerFactory = null)
    {
        return new PromptTemplateEngine(loggerFactory);
    }
}
