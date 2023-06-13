// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

internal sealed class DeleteSchemaRequest
{
    private readonly string _class;

    private DeleteSchemaRequest(string @class)
    {
        this._class = @class;
    }

    public static DeleteSchemaRequest Create(string @class)
    {
        return new(@class);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateDeleteRequest($"schema/{this._class}");
    }
}
