// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// $$$
/// </summary>
public sealed class Assistant2 : IAssistant
{
    /// <inheritdoc/>
    public string Id { get; private set; }

    private readonly IOpenAIRestContext _restContext;

    /// <summary>
    /// $$$
    /// </summary>
    internal static async Task<Assistant2> CreateAsync(
        IOpenAIRestContext restContext,
        AssistantModel assistantModel,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.CreateAssistantAsync(assistantModel, cancellationToken).ConfigureAwait(false) ??
            throw new InvalidOperationException("$$$");

        return new Assistant2(resultModel.Id, restContext);
    }

    /// <summary>
    /// $$$
    /// </summary>
    internal Assistant2(string id, IOpenAIRestContext restContext)
    {
        this.Id = id;
        this._restContext = restContext;
    }
}
