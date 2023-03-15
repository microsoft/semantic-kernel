// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Template exception.
/// </summary>
public class TemplateException : Exception<TemplateException.ErrorCodes>
{
    /// <summary>
    /// Error codes for <see cref="TemplateException"/>.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown/undefined error type. Don't use this value.
        /// </summary>
        Unknown = -1,

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

    /// <summary>
    /// Error code.
    /// </summary>
    public ErrorCodes ErrorCode { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TemplateException"/> class.
    /// </summary>
    /// <param name="errCode">The template error type.</param>
    /// <param name="message">The exception message.</param>
    public TemplateException(ErrorCodes errCode, string? message = null)
        : base(errCode, message)
    {
        this.ErrorCode = errCode;
    }

    /// <summary>
    /// Construct an exception with an error code, message, and existing exception.
    /// </summary>
    /// <param name="errCode">Error code of the exception.</param>
    /// <param name="message">Message of the exception.</param>
    /// <param name="e">An exception that was thrown.</param>
    public TemplateException(ErrorCodes errCode, string message, Exception? e) : base(errCode, message, e)
    {
        this.ErrorCode = errCode;
    }

    #region private ================================================================================

    private TemplateException()
    {
        // Not allowed, error code is required
    }

    private TemplateException(string message) : base(message)
    {
        // Not allowed, error code is required
    }

    private TemplateException(string message, Exception innerException) : base(message, innerException)
    {
        // Not allowed, error code is required
    }

    #endregion
}
