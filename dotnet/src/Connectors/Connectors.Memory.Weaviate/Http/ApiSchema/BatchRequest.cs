// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

internal sealed class BatchRequest
{
    private readonly string _class;

    private BatchRequest(string @class)
    {
        this._class = @class;
        this.Objects = new();
    }

    // ReSharper disable once UnusedMember.Global
    public string[] Fields { get; } = { "ALL" };

    // ReSharper disable once MemberCanBePrivate.Global
    // ReSharper disable once CollectionNeverQueried.Global
    public List<WeaviateObject> Objects { get; set; }

    public static BatchRequest Create(string @class)
    {
        return new(@class);
    }

    public void Add(MemoryRecord record)
    {
        record.Key = ToWeaviateFriendlyId(record.Metadata.Id);

        WeaviateObject weaviateObject = new()
        {
            Class = this._class,
            Id = record.Key,
            Vector = record.Embedding,
            Properties = new()
            {
                { "sk_timestamp", record.Timestamp! },
                { "sk_id", record.Metadata.Id },
                { "sk_description", record.Metadata.Description },
                { "sk_text", record.Metadata.Text },
                { "sk_additional_metadata", record.Metadata.AdditionalMetadata }
            }
        };

        this.Objects.Add(weaviateObject);
    }

    private static string ToWeaviateFriendlyId(string id)
    {
        return $"{id.Trim().Replace(' ', '-').Replace('/', '_').Replace('\\', '_').Replace('?', '_').Replace('#', '_')}";
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(
            "batch/objects",
            this);
    }
}
