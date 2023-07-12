// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Services.Diagnostics;

public class OrchestrationException : MemoryException
{
    /// <inheritdoc />
    public OrchestrationException() : base() { }

    /// <inheritdoc />
    public OrchestrationException(string message) : base(message) { }

    /// <inheritdoc />
    public OrchestrationException(string message, Exception? innerException) : base(message, innerException) { }
}
