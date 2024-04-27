// Copyright (c) Microsoft. All rights reserved.

namespace ContentSafety.Exceptions;

public class AttackDetectionException : Exception
{
    public AttackDetectionException()
    {
    }

    public AttackDetectionException(string? message) : base(message)
    {
    }

    public AttackDetectionException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
