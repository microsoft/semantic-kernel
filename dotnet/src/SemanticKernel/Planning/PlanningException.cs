// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Planning exception.
/// </summary>
public class PlanningException : Exception<PlanningException.ErrorCodes>
{
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
        /// Invalid plan.
        /// </summary>
        InvalidPlan = 0,

        /// <summary>
        /// Invalid configuration.
        /// </summary>
        InvalidConfiguration = 1,
    }

    /// <summary>
    /// Gets the error code of the exception.
    /// </summary>
    public ErrorCodes ErrorCode { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanningException"/> class.
    /// </summary>
    /// <param name="errCode">The error code.</param>
    /// <param name="message">The message.</param>
    public PlanningException(ErrorCodes errCode, string? message = null) : base(errCode, message)
    {
        this.ErrorCode = errCode;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanningException"/> class.
    /// </summary>
    /// <param name="errCode">The error code.</param>
    /// <param name="message">The message.</param>
    /// <param name="e">The inner exception.</param>
    public PlanningException(ErrorCodes errCode, string message, Exception? e) : base(errCode, message, e)
    {
        this.ErrorCode = errCode;
    }

    #region private ================================================================================

    private PlanningException()
    {
        // Not allowed, error code is required
    }

    private PlanningException(string message) : base(message)
    {
        // Not allowed, error code is required
    }

    private PlanningException(string message, Exception innerException) : base(message, innerException)
    {
        // Not allowed, error code is required
    }

    #endregion
}
