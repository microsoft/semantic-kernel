// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents an interface for retrieving various endpoints related to OpenAI api.
/// </summary>
internal interface IEndpointProvider
{
    /// <summary>
    /// Represents the endpoint for moderation related functionality in the OpenAI API.
    /// </summary>
    Uri ModerationEndpoint { get; }
}
