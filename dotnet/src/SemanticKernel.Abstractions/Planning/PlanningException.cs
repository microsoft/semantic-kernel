// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Planning;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown for errors related to planning.
/// </summary>
public class PlanningException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PlanningException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public PlanningException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanningException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public PlanningException(ErrorCodes errorCode, string? message = null, Exception? innerException = null)
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
            ErrorCodes.InvalidGoal => "Invalid goal",
            ErrorCodes.InvalidPlan => "Invalid plan",
            ErrorCodes.InvalidConfiguration => "Invalid configuration",
            ErrorCodes.CreatePlanError => "Create plan error",
            _ => $"Unknown error ({errorCode:G})",
        };

        return message is not null ? $"{description}: {message}" : description;
    }

    /// <summary>
    /// Error codes for <see cref="PlanningException"/>.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Invalid goal.
        /// </summary>
        InvalidGoal,

        /// <summary>
        /// Invalid plan.
        /// </summary>
        InvalidPlan,

        /// <summary>
        /// Invalid configuration.
        /// </summary>
        InvalidConfiguration,

        /// <summary>
        /// Create plan error.
        /// </summary>
        CreatePlanError,
    }
}
