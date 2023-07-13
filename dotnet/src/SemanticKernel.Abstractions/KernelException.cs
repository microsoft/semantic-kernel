// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown for errors related to kernel logic.
/// </summary>
public class KernelException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public KernelException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public KernelException(ErrorCodes errorCode, string? message = null, Exception? innerException = null)
        : base(GetDefaultMessage(errorCode, message), innerException)
    {
        this.ErrorCode = errorCode;
    }

    /// <summary>
    /// Gets the error code for this exception.
    /// </summary>
    public ErrorCodes ErrorCode { get; }

    /// <summary>Translate the error code into a default message.</summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="defaultMessage">Default error message if nothing available.</param>
    private static string GetDefaultMessage(ErrorCodes errorCode, string? defaultMessage)
    {
        string description = errorCode switch
        {
            ErrorCodes.InvalidFunctionDescription => "Invalid function description",
            ErrorCodes.FunctionOverloadNotSupported => "Function overload not supported",
            ErrorCodes.FunctionNotAvailable => "Function not available",
            ErrorCodes.FunctionTypeNotSupported => "Function type not supported",
            ErrorCodes.InvalidFunctionType => "Invalid function type",
            ErrorCodes.InvalidServiceConfiguration => "Invalid service configuration",
            ErrorCodes.ServiceNotFound => "Service not found",
            ErrorCodes.SkillCollectionNotSet => "Skill collection not set",
            ErrorCodes.FunctionInvokeError => "Function invoke error",
            _ => $"Unknown error ({errorCode:G})",
        };

        return defaultMessage is not null ? $"{description}: {defaultMessage}" : description;
    }

    /// <summary>
    /// Semantic kernel error codes.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Invalid function description.
        /// </summary>
        InvalidFunctionDescription,

        /// <summary>
        /// Function overload not supported.
        /// </summary>
        FunctionOverloadNotSupported,

        /// <summary>
        /// Function not available.
        /// </summary>
        FunctionNotAvailable,

        /// <summary>
        /// Function type not supported.
        /// </summary>
        FunctionTypeNotSupported,

        /// <summary>
        /// Invalid function type.
        /// </summary>
        InvalidFunctionType,

        /// <summary>
        /// Invalid service configuration.
        /// </summary>
        InvalidServiceConfiguration,

        /// <summary>
        /// Service not found.
        /// </summary>
        ServiceNotFound,

        /// <summary>
        /// Skill collection not set.
        /// </summary>
        SkillCollectionNotSet,

        /// <summary>
        /// Represents an error that occurs when invoking a function.
        /// </summary>
        FunctionInvokeError,
    }
}
