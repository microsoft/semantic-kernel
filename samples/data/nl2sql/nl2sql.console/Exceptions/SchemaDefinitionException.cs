// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Exceptions;

using System;
using System.Runtime.Serialization;

/// <summary>
/// Respresents a failure reading a serialized schema definition.
/// </summary>
[Serializable]
public class SchemaDefinitionException : Exception
{
    public SchemaDefinitionException()
    {
    }

    public SchemaDefinitionException(string? message)
        : base(message)
    {
    }

    public SchemaDefinitionException(string? message, Exception? innerException)
        : base(message, innerException)
    {
    }

    protected SchemaDefinitionException(SerializationInfo info, StreamingContext context)
        : base(info, context)
    {
    }
}
