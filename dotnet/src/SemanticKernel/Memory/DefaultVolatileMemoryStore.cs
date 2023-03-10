// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Default constructor for a simple volatile memory embeddings store for embeddings.
/// The default embedding type is <see cref="float"/>.
/// </summary>
public class DefaultVolatileMemoryStore : VolatileMemoryStore<float>
{
}
