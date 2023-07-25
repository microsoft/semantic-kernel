// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.UnitTests;

internal sealed class MockSKContext : SKContext
{
    private CultureInfo _culture;
    private bool _errorOccurred = false;
    private Exception? _lastException;
    private string _lastErrorDescription = string.Empty;
    private IReadOnlyCollection<ModelResult> _modelResults = Array.Empty<ModelResult>();
    private ContextVariables _variables = new();
    private IReadOnlySkillCollection _skills;
    private ILogger _logger = NullLogger.Instance;

    public override string Result => this.Variables.ToString();

    public override bool ErrorOccurred => this._errorOccurred;

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

    internal MockSKContext(
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

    internal MockSKContext(SKContext other)
        : this(other.Variables, other.Skills, other.Culture, other.ModelResults, other.Logger)
    {
    }

    public override string ToString()
    {
        return this.ErrorOccurred ? $"Error: {this.LastErrorDescription}" : this.Result;
    }

    public override SKContext Clone()
    {
        var clone = new MockSKContext(
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
}
