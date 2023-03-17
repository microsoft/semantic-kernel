// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

internal class CollectionData
{
    public string? CollectionName {get; set;}
    public QdrantResponse? CollectionResponse {get; set;}

}