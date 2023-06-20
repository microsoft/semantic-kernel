// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

internal sealed class CreateClassSchemaRequest
{
    private CreateClassSchemaRequest(string @class, string description)
    {
        this.Class = @class;
        this.Description = description;
        this.Vectorizer = "none";
        // See: MemoryRecordMetadata, we also store the timestamp
        this.Properties = new[]
        {
            new Property
            {
                Name = "sk_timestamp",
                DataType = new[] { "date" }
            },
            new Property
            {
                Name = "sk_id",
                DataType = new[] { "string" },
                IndexInverted = false
            },
            new Property
            {
                Name = "sk_description",
                DataType = new[] { "string" },
                IndexInverted = false
            },
            new Property
            {
                Name = "sk_text",
                DataType = new[] { "string" },
                IndexInverted = false
            },
            new Property
            {
                Name = "sk_additional_metadata",
                DataType = new[] { "string" },
                IndexInverted = false
            }
        };
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
