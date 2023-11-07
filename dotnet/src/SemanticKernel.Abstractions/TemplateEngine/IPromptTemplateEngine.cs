// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Prompt template engine interface.
/// </summary>
[Obsolete("PromptTemplateEngine has been replaced with PromptTemplateFactory and will be null. If you pass an PromptTemplateEngine instance when creating a Kernel it will be wrapped in an instance of IPromptTemplateFactory. This will be removed in a future release.")]
[EditorBrowsable(EditorBrowsableState.Never)]
public interface IPromptTemplateEngine
{
    /// <summary>
    /// Given a prompt template, replace the variables with their values and execute the functions replacing their
    /// reference with the function result.
    /// </summary>
    /// <param name="templateText">Prompt template (see skprompt.txt files)</param>
    /// <param name="context">Access into the current kernel execution context</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The prompt template ready to be used for an AI request</returns>
    Task<string> RenderAsync(
        string templateText,
        SKContext context,
        CancellationToken cancellationToken = default);
}
