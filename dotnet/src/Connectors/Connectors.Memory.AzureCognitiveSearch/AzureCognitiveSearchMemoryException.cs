// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown by the Azure Cognitive Search connector
/// </summary>
public class AzureCognitiveSearchMemoryException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureCognitiveSearchMemoryException"/> class.
    /// </summary>
    /// <param name="message">Exception message.</param>
    public AzureCognitiveSearchMemoryException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureCognitiveSearchMemoryException"/> class.
    /// </summary>
    /// <param name="message">Exception message.</param>
    /// <param name="innerException">Inner exception.</param>
    public AzureCognitiveSearchMemoryException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
