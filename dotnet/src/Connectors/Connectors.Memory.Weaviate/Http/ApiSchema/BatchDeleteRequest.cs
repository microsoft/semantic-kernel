// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class BatchDeleteRequest
{
    private readonly string _class;
    private readonly string[] _ids;

    private BatchDeleteRequest(string @class, string[] ids)
    {
        this._class = @class;
        this._ids = ids;
    }

    public static BatchDeleteRequest Create(string @class, string[] ids)
    {
        var friendlyIds = ids.Select(ToWeaviateFriendlyId).ToArray();
        return new(@class, friendlyIds);
    }

    private static string ToWeaviateFriendlyId(string id)
    {
        return $"{id.Trim().Replace(' ', '-').Replace('/', '_').Replace('\\', '_').Replace('?', '_').Replace('#', '_')}";
    }

    public HttpRequestMessage Build()
    {
        var body = new
        {
            match = new
            {
                @class = this._class,
                where = new
                {
                    @operator = "ContainsAny",
                    path = new[] { "id" },
                    valueStringArray = this._ids
                }
            },
            dryRun = false,
        };
        return HttpRequest.CreateDeleteBatchRequest(
            "batch/objects",
            body);
    }
}
