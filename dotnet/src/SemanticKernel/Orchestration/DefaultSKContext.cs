// Copyright (c) Microsoft. All rights reserved.

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
    public override CultureInfo Culture { get; }
    public override ContextVariables Variables { get; }
    public override IReadOnlySkillCollection Skills { get; }
    public override ILogger Logger { get; }

    public override IReadOnlyList<ModelResult> ModelResults { get; set; }

    internal DefaultSKContext(
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

    internal DefaultSKContext(SKContext other)
        : this(other.Variables, other.Skills, other.Culture, other.Logger)
    {
    }

    public override SKContext Clone()
    {
        var clone = new DefaultSKContext(this)
        {
            ModelResults = this.ModelResults
        };

        if (this.ErrorOccurred)
        {
            clone.Fail(this.LastErrorDescription ?? string.Empty, this.LastException);
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
