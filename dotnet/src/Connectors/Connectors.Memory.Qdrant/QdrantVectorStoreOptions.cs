<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Options when creating a <see cref="QdrantVectorStore"/>.
/// </summary>
public sealed class QdrantVectorStoreOptions
{
    /// <summary>
    /// Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector per qdrant point.
    /// Defaults to single vector per point.
    /// </summary>
    public bool HasNamedVectors { get; set; } = false;

    /// <summary>
    /// An optional factory to use for constructing <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
    /// An optional factory to use for constructing <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> instances, if custom options are required.
=======
>>>>>>> ms/features/bugbash-prep
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// </summary>
    public IQdrantVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
