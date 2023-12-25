// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Chroma;

internal sealed class ListCollectionsRequest
{
    public static ListCollectionsRequest Create() => new();

    public static HttpRequestMessage Build() => HttpRequest.CreateGetRequest("collections");

    private ListCollectionsRequest() { }
}
