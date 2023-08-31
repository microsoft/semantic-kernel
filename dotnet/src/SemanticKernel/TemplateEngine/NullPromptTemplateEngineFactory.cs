// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Implementation of IPromptTemplateEngineFactory which returns the provided instance of IPromptTemplateEngine.
///
/// This is a temporary solution to avoid breaking existing clients.
/// </summary>
internal sealed class NullPromptTemplateEngineFactory : IPromptTemplateEngineFactory
{
    private IPromptTemplateEngine _engine;

    internal NullPromptTemplateEngineFactory(IPromptTemplateEngine engine)
    {
        if (engine is null)
        {
            throw new ArgumentException("Prompt template engine must not be null.", nameof(engine));
        }

        this._engine = engine;
    }

    public IPromptTemplateEngine Create(string format, ILoggerFactory? loggerFactory = null)
    {
        return this._engine;
    }
}
