// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class CreateClassSchemaRequest
{
    private CreateClassSchemaRequest(string @class, string description)
    {
        this.Class = @class;
        this.Description = description;
        this.Vectorizer = "none";
        // See: MemoryRecordMetadata, we also store the timestamp
        this.Properties =
        [
            new Property
            {
                Name = "sk_timestamp",
                DataType = ["date"]
            },
            new Property
            {
                Name = "sk_id",
                DataType = ["string"],
                IndexInverted = false
            },
            new Property
            {
                Name = "sk_description",
                DataType = ["string"],
                IndexInverted = false
            },
            new Property
            {
                Name = "sk_text",
                DataType = ["string"],
                IndexInverted = false
            },
            new Property
            {
                Name = "sk_additional_metadata",
                DataType = ["string"],
                IndexInverted = false
            }
        ];
    }

    public string Class { get; set; }

    public string Description { get; set; }

    // ReSharper disable once IdentifierTypo
    public string Vectorizer { get; set; }

    public Property[] Properties { get; set; }

    public static CreateClassSchemaRequest Create(string @class, string description)
    {
        return new(@class, description);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(
            "schema",
            this);
    }
}
