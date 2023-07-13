// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Services.Diagnostics;

public class ContentStorageException : MemoryException
{
    /// <inheritdoc />
    public ContentStorageException() : base() { }

    /// <inheritdoc />
    public ContentStorageException(string message) : base(message) { }

    /// <inheritdoc />
    public ContentStorageException(string message, Exception? innerException) : base(message, innerException) { }
}
