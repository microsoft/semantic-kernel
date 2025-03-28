// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Configuration for the behavior of Pinecone's internal metadata index. By default, all metadata is indexed; when metadata_config is present, only specified metadata fields are indexed.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public class MetadataIndexConfig
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MetadataIndexConfig" /> class.
    /// </summary>
    /// <param name="indexed">indexed.</param>
    public MetadataIndexConfig(List<string> indexed)
    {
        this.Indexed = indexed;
    }

    /// <summary>
    /// The list of metadata fields to index. If not specified, all metadata fields are indexed.
    /// </summary>
    [JsonPropertyName("indexed")]
    public List<string> Indexed { get; set; }

    /// <summary>
    ///  Default metadata index configuration which is meant to align with the properties of the MemoryRecordMetadata.
    /// </summary>
    /// <remarks>
    ///  The default configuration is:
    ///  <list type="bullet">
    ///   <item>
    ///     <term>document_Id</term>
    ///     <description>Unique identifier of the document</description>
    ///     <see cref="PineconeDocument.DocumentId"/>
    ///  </item>
    ///    <item>
    ///     <term>source</term>
    ///     <description>Source of the document</description>
    ///     <see cref="MemoryRecordMetadata.ExternalSourceName"/>
    ///    </item>
    ///     <item>
    ///     <term>source_Id</term>
    ///     <description>Used to identify the source of the document</description>
    ///     <see cref="PineconeDocument.SourceId"/>
    ///     </item>
    ///     <item>
    ///     <term>url</term>
    ///     <description>Url of the source if applicable</description>
    ///    </item>
    ///     <item>
    ///     <term>type</term>
    ///     <description>The type of the text i.e. html, text, code, etc.</description>
    ///    </item>
    ///     <item>
    ///     <term>tags</term>
    ///     <description>Tags associated with the document which adds better filtering capabilities</description>
    ///     </item>
    ///     <item>
    ///     <term>created_at</term>
    ///     <description>Timestamp of when the document was created</description>
    ///     <see cref="DataEntryBase.Timestamp"/>
    ///     </item>
    /// </list>
    /// </remarks>
    public static MetadataIndexConfig Default => new(new List<string>(
    [
        "document_Id",
        "source",
        "source_Id",
        "url",
        "type",
        "tags",
        "created_at"
    ]));
}
