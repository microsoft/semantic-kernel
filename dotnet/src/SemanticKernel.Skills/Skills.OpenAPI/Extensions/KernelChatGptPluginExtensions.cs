// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Resources;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;

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
    /// <param name="httpClient">Optional HttpClient to use for the request.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginSkillFromUrlAsync(
        this IKernel kernel, string skillName, Uri url, HttpClient? httpClient = null, AuthenticateRequestAsyncCallback? authCallback = null)
    {
        Verify.ValidSkillName(skillName);

        HttpResponseMessage? response = null;
        try
        {
            if (httpClient == null)
            {
                // TODO Fix this:  throwing "The inner handler has not been assigned"
                //using DefaultHttpRetryHandler retryHandler = new DefaultHttpRetryHandler(
                //  config: new HttpRetryConfig() { MaxRetryCount = 3 },
                //  log: null);

                //using HttpClient client = new HttpClient(retryHandler, false);
                using HttpClient client = new HttpClient();

                response = await client.GetAsync(url);
            }
            else
            {
                response = await httpClient.GetAsync(url);
            }

            response.EnsureSuccessStatusCode();

            string gptPluginJson = await response.Content.ReadAsStringAsync();
            string? openApiUrl = ParseOpenApiUrl(gptPluginJson);

            return await kernel.ImportOpenApiSkillFromUrlAsync(skillName, new Uri(openApiUrl), httpClient, authCallback);
        }
        finally
        {
            if (response != null)
            {
                response.Dispose();
            }
        }
    }

    /// <summary>
    /// Imports ChatGPT plugin from assembly resource.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="httpClient">Optional HttpClient to use for the request.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportChatGptPluginSkillFromResourceAsync(
        this IKernel kernel, string skillName, HttpClient? httpClient = null, AuthenticateRequestAsyncCallback? authCallback = null)
    {
        Verify.ValidSkillName(skillName);

        var type = typeof(SkillResourceNames);

        var resourceName = $"{skillName}.ai-plugin.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName);
        if (stream == null)
        {
            throw new MissingManifestResourceException($"Unable to load OpenApi skill from assembly resource '{resourceName}'.");
        }

        using StreamReader reader = new StreamReader(stream);
        string gptPluginJson = await reader.ReadToEndAsync();

        string? openApiUrl = ParseOpenApiUrl(gptPluginJson);

        return await kernel.ImportOpenApiSkillFromUrlAsync(skillName, new Uri(openApiUrl), httpClient, authCallback);
    }

    /// <summary>
    /// Imports ChatGPT plugin from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the skill directory.</param>
    /// <param name="skillDirectoryName">Name of the directory containing the selected skill.</param>
    /// <param name="httpClient">Optional HttpClient to use for the request.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> ImportChatGptPluginSkillSkillFromDirectory(
        this IKernel kernel, string parentDirectory, string skillDirectoryName, HttpClient? httpClient = null,
        AuthenticateRequestAsyncCallback? authCallback = null)
    {
        const string CHATGPT_PLUGIN_FILE = "ai-plugin.json";

        Verify.ValidSkillName(skillDirectoryName);

        var skillDir = Path.Join(parentDirectory, skillDirectoryName);
        Verify.DirectoryExists(skillDir);

        var chatGptPluginPath = Path.Join(skillDir, CHATGPT_PLUGIN_FILE);
        if (!File.Exists(chatGptPluginPath))
        {
            throw new FileNotFoundException($"No ChatGPT plugin for the specified path - {chatGptPluginPath} is found.");
        }

        kernel.Log.LogTrace("Registering Rest functions from {0} ChatGPT Plugin.", chatGptPluginPath);

        var skill = new Dictionary<string, ISKFunction>();

        using var stream = File.OpenRead(chatGptPluginPath);

        return kernel.RegisterOpenApiSkill(stream, skillDirectoryName, authCallback);
    }

    /// <summary>
    /// Imports ChatGPT plugin from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Name of the skill to register.</param>
    /// <param name="filePath">File path to the ChatGPT plugin definition.</param>
    /// <param name="httpClient">Optional HttpClient to use for the request.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> ImportChatGptPluginSkillSkillFromFile(
        this IKernel kernel, string skillName, string filePath, HttpClient? httpClient = null, AuthenticateRequestAsyncCallback? authCallback = null)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No ChatGPT plugin for the specified path - {filePath} is found.");
        }

        kernel.Log.LogTrace("Registering Rest functions from {0} ChatGPT Plugin.", filePath);

        var skill = new Dictionary<string, ISKFunction>();

        using var stream = File.OpenRead(filePath);

        return kernel.RegisterOpenApiSkill(stream, skillName, authCallback);
    }

    private static string ParseOpenApiUrl(string gptPluginJson)
    {
        JsonNode? gptPlugin = JsonObject.Parse(gptPluginJson);

        string? apiType = gptPlugin?["api"]?["type"]?.ToString();
        if (string.IsNullOrWhiteSpace(apiType) || apiType != "openapi")
        {
            throw new InvalidOperationException($"Invalid ChatGPT plugin document. Supported api types are: openapi.");
        }

        string? openApiUrl = gptPlugin?["api"]?["url"]?.ToString();
        if (string.IsNullOrWhiteSpace(openApiUrl))
        {
            throw new InvalidOperationException($"Invalid ChatGPT plugin document. OpenAPI url is missing.");
        }

        return openApiUrl;
    }
}
