<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
<<<<<<< HEAD
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Options when creating a <see cref="PineconeVectorStore"/>.
/// </summary>
public sealed class PineconeVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======
<<<<<<< main
    /// An optional factory to use for constructing <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> instances, if custom options are required.
=======
>>>>>>> ms/features/bugbash-prep
>>>>>>> main
>>>>>>> Stashed changes
    /// </summary>
    public IPineconeVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
