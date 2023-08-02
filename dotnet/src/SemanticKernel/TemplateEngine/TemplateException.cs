// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.TemplateEngine;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown for errors related to templating.
/// </summary>
public class TemplateException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="TemplateException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public TemplateException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="TemplateException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public TemplateException(ErrorCodes errorCode, string? message = null, Exception? innerException = null)
        : base(GetDefaultMessage(errorCode, message), innerException)
    {
        this.ErrorCode = errorCode;
    }

    /// <summary>
    /// Gets the error code for this exception.
    /// </summary>
    public ErrorCodes ErrorCode { get; }

    /// <summary>Translate the error code into a default message.</summary>
    private static string GetDefaultMessage(ErrorCodes errorCode, string? message)
    {
        string description = errorCode switch
        {
            ErrorCodes.SyntaxError => "Syntax error",
            ErrorCodes.UnexpectedBlockType => "Unexpected block type",
            ErrorCodes.FunctionNotFound => "Function not found",
            ErrorCodes.RuntimeError => "Runtime error",
            _ => $"Unknown error ({errorCode:G})",
        };

        return message is not null ? $"{description}: {message}" : description;
    }

    /// <summary>
    /// Error codes for <see cref="TemplateException"/>.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Syntax error, the template syntax used is not valid.
        /// </summary>
        SyntaxError = 0,

        /// <summary>
        /// The block type produced be the tokenizer was not expected
        /// </summary>
        UnexpectedBlockType = 1,

        /// <summary>
        /// The template requires an unknown function.
        /// </summary>
        FunctionNotFound = 2,

        /// <summary>
        /// The template execution failed, e.g. a function call threw an exception.
        /// </summary>
        RuntimeError = 3,
    }
}
