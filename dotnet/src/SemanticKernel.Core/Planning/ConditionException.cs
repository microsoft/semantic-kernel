// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Planning;

public class ConditionException : Exception<ConditionException.ErrorCodes>
{
    /// <summary>
    /// Error codes for <see cref="ConditionException"/>.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Invalid condition structure.
        /// </summary>
        InvalidCondition = 0,

        /// <summary>
        /// Invalid statement structure.
        /// </summary>
        InvalidStatementStructure = 1,

        /// <summary>
        /// Json Response was not present in the output
        /// </summary>
        InvalidResponse = 2,

        /// <summary>
        /// Required context variables are not present in the context
        /// </summary>
        ContextVariablesNotFound = 3,
    }

    /// <summary>
    /// Gets the error code of the exception.
    /// </summary>
    public ErrorCodes ErrorCode { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ConditionException"/> class.
    /// </summary>
    /// <param name="errCode">The error code.</param>
    /// <param name="message">The message.</param>
    public ConditionException(ErrorCodes errCode, string? message = null) : base(errCode, message)
    {
        this.ErrorCode = errCode;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ConditionException"/> class.
    /// </summary>
    /// <param name="errCode">The error code.</param>
    /// <param name="message">The message.</param>
    /// <param name="e">The inner exception.</param>
    public ConditionException(ErrorCodes errCode, string message, Exception? e) : base(errCode, message, e)
    {
        this.ErrorCode = errCode;
    }

    #region private ================================================================================

    private ConditionException()
    {
        // Not allowed, error code is required
    }

    private ConditionException(string message) : base(message)
    {
        // Not allowed, error code is required
    }

    private ConditionException(string message, Exception innerException) : base(message, innerException)
    {
        // Not allowed, error code is required
    }

    #endregion
}
