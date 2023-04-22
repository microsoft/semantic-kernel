// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Connectors.Exceptions;

/// <summary>
/// Exception thrown by the MsGraph connectors
/// </summary>
public class MsGraphConnectorException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MsGraphConnectorException"/> class.
    /// </summary>
    /// <param name="message">Exception message.</param>
    public MsGraphConnectorException(string message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MsGraphConnectorException"/> class.
    /// </summary>
    /// <param name="message">Exception message.</param>
    /// <param name="innerException">Inner exception.</param>
    public MsGraphConnectorException(string message, Exception innerException) : base(message, innerException)
    {
    }

    private MsGraphConnectorException()
    {
        // Do not use, error message is required
    }
}
