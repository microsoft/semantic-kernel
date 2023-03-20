// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

internal class CollectionData
{
    public string CollectionName { get; set; } = string.Empty;
    public QdrantResponse CollectionResponse { get; set; } = default!;


}

