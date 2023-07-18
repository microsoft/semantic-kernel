// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Exceptions;

using System;
using System.Runtime.Serialization;

/// <summary>
/// Represents a failure or unexpected condition parsing the result of a semantic function.
/// </summary>
[Serializable]
public class ResultParsingException : Exception
{
    public ResultParsingException()
    {
    }

    public ResultParsingException(string? message)
        : base(message)
    {
    }

    public ResultParsingException(string? message, Exception? innerException)
        : base(message, innerException)
    {
    }

    protected ResultParsingException(SerializationInfo info, StreamingContext context)
        : base(info, context)
    {
    }
}
