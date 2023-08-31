// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// No-operation IPromptTemplateEngine which performs no rendering of the template.
///
/// This is a temporary solution to avoid breaking existing clients.
/// </summary>
internal class NullPromptTemplateEngine : IPromptTemplateEngine
{
    private readonly ILoggerFactory _loggerFactory;
    private readonly ILogger _logger;

    public NullPromptTemplateEngine(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._logger = this._loggerFactory.CreateLogger(nameof(NullPromptTemplateEngine));
    }

    public Task<string> RenderAsync(string templateText, SKContext context, CancellationToken cancellationToken = default)
    {
        this._logger.LogTrace("Rendering string template: {0}", templateText);
        return Task.FromResult(templateText);
    }
}
