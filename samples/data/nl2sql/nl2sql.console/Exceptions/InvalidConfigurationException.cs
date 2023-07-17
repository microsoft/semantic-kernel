// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Exceptions;

using System;
using System.Runtime.Serialization;

/// <summary>
/// Respresents a missing or unexpected configuration setting.
/// </summary>
[Serializable]
public class InvalidConfigurationException : Exception
{
    public InvalidConfigurationException()
    {
    }

    public InvalidConfigurationException(string? message)
        : base(message)
    {
    }

    public InvalidConfigurationException(string? message, Exception? innerException)
        : base(message, innerException)
    {
    }

    protected InvalidConfigurationException(SerializationInfo info, StreamingContext context)
        : base(info, context)
    {
    }
}
