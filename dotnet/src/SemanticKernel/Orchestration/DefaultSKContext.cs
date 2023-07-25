// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Semantic Kernel context.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed class DefaultSKContext : SKContext
{
    private CultureInfo _culture;
    private bool _errorOccurred = false;
    private Exception? _lastException;
    private string _lastErrorDescription = string.Empty;
    private IReadOnlyCollection<ModelResult> _modelResults;
    private ContextVariables _variables;
    private IReadOnlySkillCollection _skills;
    private ILogger _logger;

    internal static SKContext FromException(Exception exception)
    {
        DefaultSKContext context = new();
        context.Fail(exception.Message, exception);
        return context;
    }

    public override string Result => this.Variables.ToString();

    public override bool ErrorOccurred => this._lastException != null;

    public override string LastErrorDescription => this._lastErrorDescription;

    public override Exception? LastException => this._lastException;

    public override IReadOnlyCollection<ModelResult> ModelResults => this._modelResults;

    public override CultureInfo Culture
    {
        get => this._culture;
    }

    public override void Fail(string errorDescription, Exception? exception = null)
    {
        this._errorOccurred = true;
        this._lastErrorDescription = errorDescription;
        this._lastException = exception;
    }

    public override ContextVariables Variables => this._variables;

    public override IReadOnlySkillCollection Skills => this._skills;

    public override ILogger Logger => this._logger;

    internal DefaultSKContext(
        ContextVariables? variables = null,
        IReadOnlySkillCollection? skills = null,
        CultureInfo? culture = null,
        IReadOnlyCollection<ModelResult>? modelResults = null,
        ILogger? logger = null)
    {
        this._variables = variables ?? new();
        this._skills = skills ?? new SkillCollection();
        this._culture = culture ?? CultureInfo.CurrentCulture;
        this._modelResults = modelResults ?? Array.Empty<ModelResult>();
        this._logger = logger ?? NullLogger.Instance;
    }

    internal DefaultSKContext(SKContext other)
        : this(other.Variables, other.Skills, other.Culture, other.ModelResults, other.Logger)
    {
    }

    public override string ToString()
    {
        return this.ErrorOccurred ? $"Error: {this.LastErrorDescription}" : this.Result;
    }

    public override SKContext Clone()
    {
        var clone = new DefaultSKContext(
            variables: this.Variables.Clone(),
            skills: this.Skills,
            culture: this.Culture,
            logger: this.Logger);

        if (this.ErrorOccurred)
        {
            clone.Fail(this.LastErrorDescription, this.LastException);
        };

        return clone;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay
    {
        get
        {
            if (this.ErrorOccurred)
            {
                return $"Error: {this.LastErrorDescription}";
            }

            string display = this.Variables.DebuggerDisplay;

            if (this.Skills is IReadOnlySkillCollection skills)
            {
                var view = skills.GetFunctionsView();
                display += $", Skills = {view.NativeFunctions.Count + view.SemanticFunctions.Count}";
            }

            display += $", Culture = {this.Culture.EnglishName}";

            return display;
        }
    }
}
