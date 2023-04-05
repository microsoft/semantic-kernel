// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;

/// <summary>
/// Exception to be throw in case parsing of OpenApi document failed. E.g. mandatory property is missing or empty, value is out of range
/// </summary>
public class OpenApiDocumentParsingException : Exception
{
    /// <summary>
    /// Creates an instance of a <see cref="OpenApiDocumentParsingException"/> class.
    /// </summary>
    /// <param name="message">The exception message.</param>
    public OpenApiDocumentParsingException(string message) : base(message)
    {
    }

    /// <summary>
    /// Creates an instance of a <see cref="OpenApiDocumentParsingException"/> class.
    /// </summary>
    /// <param name="message">The exception message.</param>
    /// <param name="innerException">The inner exception.</param>
    public OpenApiDocumentParsingException(string message, Exception innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Creates an instance of a <see cref="OpenApiDocumentParsingException"/> class.
    /// </summary>
    public OpenApiDocumentParsingException()
    {
    }
}
