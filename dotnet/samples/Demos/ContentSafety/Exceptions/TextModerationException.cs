// Copyright (c) Microsoft. All rights reserved.

namespace ContentSafety.Exceptions;

public class TextModerationException : Exception
{
    public TextModerationException()
    {
    }

    public TextModerationException(string? message) : base(message)
    {
    }

    public TextModerationException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
