// Copyright (c) Microsoft. All rights reserved.

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
        /// Unknown.
        /// </summary>
        Unknown = -1,

        /// <summary>
        /// Syntax error.
        /// </summary>
        SyntaxError = 0,
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
}
