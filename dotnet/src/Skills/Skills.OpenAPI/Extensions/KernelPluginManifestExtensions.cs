// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods for IKernel interface.
/// </summary>
public static class KernelPluginManifestExtensions
{
    /// <summary>
    /// Imports plugin manifest document from a URL.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="url">Url to in which to retrieve the plugin manifest.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A dictionary of all the plugins and their functions that were imported.</returns>
    public static async Task<IDictionary<string, ISKFunction>?> ImportPluginManifestFromUrlAsync(
        this IKernel kernel,
        Uri url,
        CancellationToken cancellationToken = default)
    {
        using var internalHttpClient = HttpClientProvider.GetHttpClient(kernel.Config, null, kernel.Log);

        using HttpResponseMessage response = await internalHttpClient.GetAsync(url, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        string pluginJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        var pluginManifest = ParsePluginJson(pluginJson);

        Dictionary<string, ISKFunction> functions = new();

        foreach (var plugin in pluginManifest.Plugins)
        {
            var result = await kernel.ImportChatGptPluginSkillFromUrlAsync(plugin.Value.Functions.FirstOrDefault().SkillName, plugin.Value.Url, null, cancellationToken).ConfigureAwait(false);
            foreach (var function in result)
            {
                functions.Add(function.Key, function.Value);
            }
        }

        return functions;
    }

    /// <summary>
    /// Imports plugin manifest document from a string.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginManifestJson">Plugin manifest json.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A dictionary of all the plugins and their functions that were imported.</returns>
    public static async Task<IDictionary<string, ISKFunction>?> ImportPluginManifestAsync(
        this IKernel kernel,
        string pluginManifestJson,
        CancellationToken cancellationToken = default)
    {
        var pluginManifest = ParsePluginJson(pluginManifestJson);

        Dictionary<string, ISKFunction> functions = new();

        foreach (var plugin in pluginManifest.Plugins)
        {
            var result = await kernel.ImportChatGptPluginSkillFromUrlAsync(plugin.Value.Functions.FirstOrDefault().SkillName, plugin.Value.Url, null, cancellationToken).ConfigureAwait(false);
            foreach (var function in result)
            {
                functions.Add(function.Key, function.Value);
            }
        }

        return functions;
    }

    private static PluginManifest ParsePluginJson(string pluginJson)
    {
        return JsonSerializer.Deserialize<PluginManifest>(pluginJson) ?? throw new InvalidOperationException("Invalid plugin manifest");
    }
}
