// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

/// <summary>
/// A plugin manifest that lists plugins and their names.
/// </summary>
public sealed class PluginManifest
{
    /// <summary>
    /// The list of plugins.
    /// </summary>
    public Dictionary<string, RemotePlugin> Plugins { get; set; } = new Dictionary<string, RemotePlugin>();
}

/// <summary>
/// A remote plugin definition.
/// </summary>
public sealed class RemotePlugin
{
    /// <summary>
    /// The functions available in the remote plugin.
    /// </summary>
    public List<FunctionView> Functions { get; set; } = new List<FunctionView>();

    /// <summary>
    /// The URL of the remote plugin.
    /// </summary>
    public Uri Url { get; set; } = null!;
}
