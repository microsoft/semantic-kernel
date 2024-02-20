// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// Exception thrown by the AssemblyAI API.
/// </summary>
public class AssemblyAIApiException : Exception
{
    /// <inheritdoc />
    public AssemblyAIApiException() : base()
    {
    }

    /// <inheritdoc />
    public AssemblyAIApiException(string message) : base(message)
    {
    }

    /// <inheritdoc />
    public AssemblyAIApiException(string message, Exception innerException) : base(message, innerException)
    {
    }
}
