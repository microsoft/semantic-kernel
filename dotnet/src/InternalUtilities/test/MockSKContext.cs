// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.UnitTests;

internal sealed class MockSKContext : SKContext
{
    private Exception? _exception = null;

    public override CultureInfo Culture { get; }
    public override ContextVariables Variables { get; }
    public override IReadOnlySkillCollection Skills { get; }
    public override ILogger Logger { get; }
    public override IReadOnlyList<ModelResult> ModelResults { get; set; } = new List<ModelResult>();
    public override bool ErrorOccurred => this._exception != null;
    public override Exception? LastException => this._exception;

    public override MockSKContext Clone()
    {
        var clone = new MockSKContext(this)
        {
            ModelResults = this.ModelResults
        };

        if (this.ErrorOccurred)
        {
            clone._exception = this.LastException;
        };

        return clone;
    }

    internal MockSKContext(
       ContextVariables? variables = null,
       IReadOnlySkillCollection? skills = null,
       CultureInfo? culture = null,
       ILogger? logger = null)
    {
        this.Variables = variables ?? new();
        this.Skills = skills ?? new SkillCollection();
        this.Culture = culture ?? CultureInfo.CurrentCulture;
        this.Logger = logger ?? NullLogger.Instance;
    }

    internal MockSKContext(SKContext other)
        : this(other.Variables, other.Skills, other.Culture, other.Logger)
    {
    }

    internal void SetException(Exception exception)
    {
        this._exception = exception;
    }

    /// <inheritdoc/>
    [Obsolete("Throw exception from SKFunction implementation instead. The Kernel will set the failure properties. " +
        "This method will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public override SKContext Fail(string errorDescription, Exception? exception = null)
    {
        // Temporary workaround: if no exception is provided, create a new one.
        this.SetException(exception ?? new KernelException(KernelException.ErrorCodes.UnknownError, errorDescription));
        return this;
    }
}
