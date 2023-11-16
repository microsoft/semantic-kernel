// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Added for backward compatibility only, this will be removed when ISKFunction.SetAIService and ISKFunction.SetAIConfiguration are removed.
/// </summary>
[Obsolete("Remove this when ISKFunction.SetAIService and ISKFunction.SetAIConfiguration are removed.")]
internal class DelegatingAIServiceSelector : IAIServiceSelector
{
    internal Func<ITextCompletion>? ServiceFactory { get; set; }
    internal AIRequestSettings? RequestSettings { get; set; }

    /// <inheritdoc/>
    public (T?, AIRequestSettings?) SelectAIService<T>(SKContext context, ISKFunction skfunction) where T : IAIService
    {
        return ((T?)this.ServiceFactory?.Invoke() ?? context.ServiceProvider.GetService<T>(null), this.RequestSettings ?? skfunction.RequestSettings);
    }
}
