// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// $$$
/// </summary>
public interface IOpenAIRestContext
{
    /// <summary>
    /// $$$
    /// </summary>
    string ApiKey { get; }

    /// <summary>
    /// $$$
    /// </summary>
    HttpClient HttpClient { get; }
}
