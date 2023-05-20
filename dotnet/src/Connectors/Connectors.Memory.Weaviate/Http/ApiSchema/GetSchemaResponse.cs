// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

internal sealed class GetSchemaResponse
{
    // ReSharper disable once CollectionNeverUpdated.Global
    public List<GetClassResponse>? Classes { get; set; }
}
