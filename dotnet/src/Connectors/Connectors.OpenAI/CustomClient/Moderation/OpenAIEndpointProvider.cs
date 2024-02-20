// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <inheritdoc />
internal sealed class OpenAIEndpointProvider : IEndpointProvider
{
    /// <inheritdoc />
    public Uri ModerationEndpoint { get; } = new("https://api.openai.com/v1/moderations");
}
