// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Context for interacting with OpenAI REST API.
/// </summary>
public interface IOpenAIRestContext
{
    /// <summary>
    /// The OpenAI API key.
    /// </summary>
    string ApiKey { get; }

    /// <summary>
    /// The http-client to utilize.
    /// </summary>
    HttpClient HttpClient { get; }
}
