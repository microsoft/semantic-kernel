// Copyright (c) Microsoft. All rights reserved.

#if !NET8_0_OR_GREATER

// Polyfill for using UnreachableException with .NET Standard 2.0

namespace System.Diagnostics;

#pragma warning disable CA1064 // Exceptions should be public
#pragma warning disable CA1812 // Internal class that is (sometimes) never instantiated.

/// <summary>
/// Exception thrown when the program executes an instruction that was thought to be unreachable.
/// </summary>
internal sealed class UnreachableException : Exception
{
    private const string MessageText = "The program executed an instruction that was thought to be unreachable.";

    /// <summary>
    /// Initializes a new instance of the <see cref="UnreachableException"/> class with the default error message.
    /// </summary>
    public UnreachableException()
        : base(MessageText)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="UnreachableException"/>
    /// class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public UnreachableException(string? message)
        : base(message ?? MessageText)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="UnreachableException"/>
    /// class with a specified error message and a reference to the inner exception that is the cause of
    /// this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public UnreachableException(string? message, Exception? innerException)
        : base(message ?? MessageText, innerException)
    {
    }
}

#endif
