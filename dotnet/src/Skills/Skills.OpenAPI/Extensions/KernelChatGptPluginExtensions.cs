// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Resources;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods for IKernel interface.
/// </summary>
public static class KernelChatGptPluginExtensions
{
    /// <summary>
    /// Imports ChatGPT plugin document from a URL.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="url">Url to in which to retrieve the ChatGPT plugin.</param>
    /// <param name="httpClient">HttpClient to use for the request.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <param name="userAgent">Optional user agent header value.</param>
    /// <param name="retryConfiguration">Optional retry configuration.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginSkillFromUrlAsync(
        this IKernel kernel,
        string skillName,
        Uri url,
        HttpClient httpClient,
        AuthenticateRequestAsyncCallback? authCallback = null,
        string? userAgent = "Microsoft-Semantic-Kernel",
        HttpRetryConfig? retryConfiguration = null,
        CancellationToken cancellationToken = default)
    {
        Verify.ValidSkillName(skillName);

        using HttpResponseMessage response = await httpClient.GetAsync(url, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        string gptPluginJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        string? openApiUrl = ParseOpenApiUrl(gptPluginJson);

        return await kernel
            .ImportOpenApiSkillFromUrlAsync(skillName, new Uri(openApiUrl), httpClient, authCallback, userAgent, retryConfiguration, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    /// <summary>
    /// Imports ChatGPT plugin from assembly resource.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="httpClient">HttpClient to use for the request.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <param name="userAgent">Optional user agent header value.</param>
    /// <param name="retryConfiguration">Optional retry configuration.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginSkillFromResourceAsync(
        this IKernel kernel,
        string skillName,
        HttpClient httpClient,
        AuthenticateRequestAsyncCallback? authCallback = null,
        string? userAgent = "Microsoft-Semantic-Kernel",
        HttpRetryConfig? retryConfiguration = null,
        CancellationToken cancellationToken = default)
    {
        Verify.ValidSkillName(skillName);

        var type = typeof(SkillResourceNames);

        var resourceName = $"{skillName}.ai-plugin.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName)
                     ?? throw new MissingManifestResourceException($"Unable to load OpenApi skill from assembly resource '{resourceName}'");

        using StreamReader reader = new(stream);
        string gptPluginJson = await reader.ReadToEndAsync().ConfigureAwait(false);

        string? openApiUrl = ParseOpenApiUrl(gptPluginJson);

        return await kernel
            .ImportOpenApiSkillFromUrlAsync(skillName, new Uri(openApiUrl), httpClient, authCallback, userAgent, retryConfiguration, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    /// <summary>
    /// Imports ChatGPT plugin from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the skill directory.</param>
    /// <param name="skillDirectoryName">Name of the directory containing the selected skill.</param>
    /// <param name="httpClient">Optional HttpClient to use for the request.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <param name="retryConfiguration">Optional retry configuration.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginSkillSkillFromDirectoryAsync(
        this IKernel kernel,
        string parentDirectory,
        string skillDirectoryName,
        HttpClient? httpClient = null,
        AuthenticateRequestAsyncCallback? authCallback = null,
        HttpRetryConfig? retryConfiguration = null,
        CancellationToken cancellationToken = default)
    {
        const string ChatGptPluginFile = "ai-plugin.json";

        Verify.ValidSkillName(skillDirectoryName);

        var skillDir = Path.Combine(parentDirectory, skillDirectoryName);
        Verify.DirectoryExists(skillDir);

        var chatGptPluginPath = Path.Combine(skillDir, ChatGptPluginFile);
        if (!File.Exists(chatGptPluginPath))
        {
            throw new FileNotFoundException($"No ChatGPT plugin for the specified path - {chatGptPluginPath} is found");
        }

        kernel.Log.LogTrace("Registering Rest functions from {0} ChatGPT Plugin", chatGptPluginPath);

        using var stream = File.OpenRead(chatGptPluginPath);

        return await kernel
            .RegisterOpenApiSkillAsync(stream, skillDirectoryName, authCallback, retryConfiguration, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    /// <summary>
    /// Imports ChatGPT plugin from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Name of the skill to register.</param>
    /// <param name="filePath">File path to the ChatGPT plugin definition.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <param name="retryConfiguration">Optional retry configuration.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginSkillSkillFromFileAsync(
        this IKernel kernel,
        string skillName,
        string filePath,
        AuthenticateRequestAsyncCallback? authCallback = null,
        HttpRetryConfig? retryConfiguration = null,
        CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No ChatGPT plugin for the specified path - {filePath} is found");
        }

        kernel.Log.LogTrace("Registering Rest functions from {0} ChatGPT Plugin", filePath);

        using var stream = File.OpenRead(filePath);

        return await kernel
            .RegisterOpenApiSkillAsync(stream, skillName, authCallback, retryConfiguration, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    private static string ParseOpenApiUrl(string gptPluginJson)
    {
        JsonNode? gptPlugin = JsonObject.Parse(gptPluginJson);

        string? apiType = gptPlugin?["api"]?["type"]?.ToString();
        if (string.IsNullOrWhiteSpace(apiType) || apiType != "openapi")
        {
            throw new InvalidOperationException("Invalid ChatGPT plugin document. Supported api types are: openapi");
        }

        string? openApiUrl = gptPlugin?["api"]?["url"]?.ToString();
        if (string.IsNullOrWhiteSpace(openApiUrl))
        {
            throw new InvalidOperationException("Invalid ChatGPT plugin document, OpenAPI URL is missing");
        }

        return openApiUrl!;
    }
}
