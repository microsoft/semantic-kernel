// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Globalization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.UnitTests;

internal sealed class MockSKContext : SKContext
{
    public override CultureInfo Culture { get; }
    public override ContextVariables Variables { get; }
    public override IReadOnlySkillCollection Skills { get; }
    public override ILogger Logger { get; }

    public override IReadOnlyList<ModelResult> ModelResults { get; set; }

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
        this.ModelResults = new List<ModelResult>();
    }

    internal MockSKContext(SKContext other)
        : this(other.Variables, other.Skills, other.Culture, other.Logger)
    {
    }

    public override SKContext Clone()
    {
        var clone = new MockSKContext(this)
        {
            ModelResults = this.ModelResults
        };

        if (this.ErrorOccurred)
        {
            clone.Fail(this.LastErrorDescription ?? string.Empty, this.LastException);
        };

        return clone;
    }
}
