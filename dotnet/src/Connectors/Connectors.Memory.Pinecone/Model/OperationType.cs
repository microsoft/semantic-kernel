// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

[Experimental("SKEXP0020")]
internal enum OperationType
{
    Upsert,
    Update,
    Skip
}
