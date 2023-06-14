// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

internal sealed class GetClassRequest
{
    private GetClassRequest(string @class)
    {
        this.Class = @class;
    }

    /// <summary>
    ///     Name of the Weaviate class
    /// </summary>
    [JsonIgnore]
    // ReSharper disable once MemberCanBePrivate.Global
    public string Class { get; set; }

    public static GetClassRequest Create(string @class)
    {
        return new(@class);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateGetRequest($"schema/{this.Class}");
    }
}
