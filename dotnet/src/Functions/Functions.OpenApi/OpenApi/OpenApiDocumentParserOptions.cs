// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Options for OpenAPI document parser.
/// </summary>
public sealed class OpenApiDocumentParserOptions
{
    /// <summary>
    /// Flag indicating whether to ignore non-compliant errors in the OpenAPI document during parsing.
    /// If set to true, the parser will not throw exceptions for non-compliant documents.
    /// Please note that enabling this option may result in incomplete or inaccurate parsing results.
    /// </summary>
    public bool IgnoreNonCompliantErrors { set; get; } = false;

    /// <summary>
    /// Operation selection predicate to apply to all OpenAPI document operations.
    /// If set, the predicate will be applied to each operation in the document.
    /// If the predicate returns true, the operation will be parsed; otherwise, it will be skipped.
    /// This can be used to filter out operations that should not be imported for various reasons.
    /// </summary>
    public Func<OperationSelectionPredicateContext, bool>? OperationSelectionPredicate { get; set; }
}
