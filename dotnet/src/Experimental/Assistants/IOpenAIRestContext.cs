// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

internal interface IOpenAIRestContext
{
    string ApiKey { get; }

    HttpClient HttpClient { get; }
}
