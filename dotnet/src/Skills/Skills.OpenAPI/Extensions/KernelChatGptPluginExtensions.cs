// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Resources;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
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
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("ChatGPT specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginFromUrlAsync(
        this IKernel kernel,
        string skillName,
        Uri url,
        OpenApiSkillExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.ValidSkillName(skillName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var internalHttpClient = HttpClientProvider.GetHttpClient(kernel.Config, executionParameters?.HttpClient, kernel.Log);
#pragma warning restore CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.

        using var requestMessage = new HttpRequestMessage(HttpMethod.Get, url);

        if (!string.IsNullOrEmpty(executionParameters?.UserAgent))
        {
            requestMessage.Headers.UserAgent.Add(ProductInfoHeaderValue.Parse(executionParameters!.UserAgent));
        }

        using var response = await internalHttpClient.SendAsync(requestMessage, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        string gptPluginJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        string? openApiUrl = ParseOpenApiUrl(gptPluginJson);

        return await kernel
            .ImportOpenApiSkillFromUrlAsync(skillName, new Uri(openApiUrl), executionParameters, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    /// <summary>
    /// Imports ChatGPT plugin from assembly resource.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("ChatGPT specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginFromResourceAsync(
        this IKernel kernel,
        string skillName,
        OpenApiSkillExecutionParameters? executionParameters = null,
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
            .ImportOpenApiSkillFromUrlAsync(skillName, new Uri(openApiUrl), executionParameters, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    /// <summary>
    /// Imports ChatGPT plugin from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the skill directory.</param>
    /// <param name="skillDirectoryName">Name of the directory containing the selected skill.</param>
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("ChatGPT specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginFromDirectoryAsync(
        this IKernel kernel,
        string parentDirectory,
        string skillDirectoryName,
        OpenApiSkillExecutionParameters? executionParameters = null,
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
            .RegisterOpenApiSkillAsync(stream, skillDirectoryName, executionParameters, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    /// <summary>
    /// Imports ChatGPT plugin from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Name of the skill to register.</param>
    /// <param name="filePath">File path to the ChatGPT plugin definition.</param>
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("ChatGPT specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginFromFileAsync(
        this IKernel kernel,
        string skillName,
        string filePath,
        OpenApiSkillExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No ChatGPT plugin for the specified path - {filePath} is found");
        }

        kernel.Log.LogTrace("Registering Rest functions from {0} ChatGPT Plugin", filePath);

        using var stream = File.OpenRead(filePath);

        return await kernel
            .RegisterOpenApiSkillAsync(stream, skillName, executionParameters, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    private static string ParseOpenApiUrl(string gptPluginJson)
    {
        JsonNode? gptPlugin = JsonNode.Parse(gptPluginJson);

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
