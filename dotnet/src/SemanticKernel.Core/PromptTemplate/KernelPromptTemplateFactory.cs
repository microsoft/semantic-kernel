// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides an implementation of <see cref="IPromptTemplateFactory"/> for the <see cref="PromptTemplateConfig.SemanticKernelTemplateFormat"/> template format.
/// </summary>
/// <remarks>
/// This is used as the default <see cref="IPromptTemplateFactory"/> when no other factory is provided.
/// </remarks>
public sealed class KernelPromptTemplateFactory : IPromptTemplateFactory
{
    private readonly ILoggerFactory _loggerFactory;

    /// <summary>
    /// Gets or sets a value indicating whether to allow potentially dangerous content to be inserted into the prompt.
    /// </summary>
    /// <remarks>
    /// The default is false.
    /// When set to true then all input content added to templates is treated as safe content.
    /// For prompts which are being used with a chat completion service this should be set to false to protect against prompt injection attacks.
    /// When using other AI services e.g. Text-To-Image this can be set to true to allow for more complex prompts.
    /// </remarks>
    public bool AllowDangerouslySetContent { get; init; } = false;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelPromptTemplateFactory"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public KernelPromptTemplateFactory(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
    }

    /// <inheritdoc/>
    public bool TryCreate(PromptTemplateConfig templateConfig, [NotNullWhen(true)] out IPromptTemplate? result)
    {
        Verify.NotNull(templateConfig);

        if (templateConfig.TemplateFormat.Equals(PromptTemplateConfig.SemanticKernelTemplateFormat, System.StringComparison.Ordinal))
        {
            result = new KernelPromptTemplate(templateConfig, this.AllowDangerouslySetContent, this._loggerFactory);
            return true;
        }

        result = null;
        return false;
    }
}
