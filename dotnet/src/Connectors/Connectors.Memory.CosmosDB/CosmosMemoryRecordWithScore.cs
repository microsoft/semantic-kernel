// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCosmosDb;
internal sealed class CosmosMemoryRecordWithScore:CosmosMemoryRecord
{
    public double Score { get; set; }
}
