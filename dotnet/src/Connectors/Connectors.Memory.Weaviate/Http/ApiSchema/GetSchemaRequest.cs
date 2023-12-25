// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal static class GetSchemaRequest
{
    public static HttpRequestMessage Build() => HttpRequest.CreateGetRequest("schema");
}
