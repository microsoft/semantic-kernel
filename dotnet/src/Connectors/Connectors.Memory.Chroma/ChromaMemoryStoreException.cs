// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

public class ChromaMemoryStoreException : Exception
{
    public ChromaMemoryStoreException() : base()
    {
    }

    public ChromaMemoryStoreException(string message) : base(message)
    {
    }

    public ChromaMemoryStoreException(string message, Exception innerException) : base(message, innerException)
    {
    }
}
