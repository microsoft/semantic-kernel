// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Adapters.Exceptions;

/// <summary>
/// Exception thrown by the MsGraph adapters
/// </summary>
public class MsGraphAdapterException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MsGraphAdapterException"/> class.
    /// </summary>
    /// <param name="message">Exception message.</param>
    public MsGraphAdapterException(string message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MsGraphAdapterException"/> class.
    /// </summary>
    /// <param name="message">Exception message.</param>
    /// <param name="innerException">Inner exception.</param>
    public MsGraphAdapterException(string message, Exception innerException) : base(message, innerException)
    {
    }

    private MsGraphAdapterException()
    {
        // Do not use, error message is required
    }
}
