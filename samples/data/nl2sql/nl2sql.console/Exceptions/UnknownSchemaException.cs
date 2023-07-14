// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Exceptions;

using System;
using System.Runtime.Serialization;

[Serializable]
public class UnknownSchemaException : Exception
{
    public UnknownSchemaException()
    {
    }

    public UnknownSchemaException(string? message)
        : base(message)
    {
    }

    public UnknownSchemaException(string? message, Exception? innerException)
        : base(message, innerException)
    {
    }

    protected UnknownSchemaException(SerializationInfo info, StreamingContext context)
        : base(info, context)
    {
    }
}
