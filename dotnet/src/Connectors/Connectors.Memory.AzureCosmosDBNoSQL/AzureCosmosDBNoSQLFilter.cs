// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Contains properties required to build query with filtering conditions.
/// </summary>
internal sealed class AzureCosmosDBNoSQLFilter
{
    public List<string>? WhereClauseArguments { get; set; }

    public Dictionary<string, object>? QueryParameters { get; set; }
}
