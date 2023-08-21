// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Resources;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods for <see cref="IKernel"/> interface.
/// </summary>
public static class KernelOpenApiExtensions
{
    /// <summary>
    /// Imports OpenAPI document from a URL.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="url">Url to in which to retrieve the OpenAPI definition.</param>
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("OpenApi specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenApiSkillFromUrlAsync(
        this IKernel kernel,
        string skillName,
        Uri url,
        OpenApiSkillExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.ValidSkillName(skillName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var internalHttpClient = HttpClientProvider.GetHttpClient(kernel.Config, executionParameters?.HttpClient, kernel.Logger);
#pragma warning restore CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.

        using var requestMessage = new HttpRequestMessage(HttpMethod.Get, url);

        requestMessage.Headers.UserAgent.Add(!string.IsNullOrEmpty(executionParameters?.UserAgent)
            ? ProductInfoHeaderValue.Parse(executionParameters!.UserAgent)
            : ProductInfoHeaderValue.Parse(Telemetry.HttpUserAgent));

        using var response = await internalHttpClient.SendAsync(requestMessage, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        var stream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
        if (stream == null)
        {
            throw new MissingManifestResourceException($"Unable to load OpenApi skill from url '{url}'.");
        }

        return await kernel.RegisterOpenApiSkillAsync(stream, skillName, executionParameters, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Imports OpenApi document from assembly resource.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("ChatGPT specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static Task<IDictionary<string, ISKFunction>> ImportOpenApiSkillFromResourceAsync(
        this IKernel kernel,
        string skillName,
        OpenApiSkillExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.ValidSkillName(skillName);

        var type = typeof(SkillResourceNames);

        var resourceName = $"{skillName}.openapi.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName); //TODO: support yaml resources
        if (stream == null)
        {
            throw new MissingManifestResourceException($"Unable to load OpenApi skill from assembly resource '{resourceName}'.");
        }

        return kernel.RegisterOpenApiSkillAsync(stream, skillName, executionParameters, cancellationToken);
    }

    /// <summary>
    /// Imports OpenApi document from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the skill directory.</param>
    /// <param name="skillDirectoryName">Name of the directory containing the selected skill.</param>
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("OpenApi specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenApiSkillFromDirectoryAsync(
        this IKernel kernel,
        string parentDirectory,
        string skillDirectoryName,
        OpenApiSkillExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        const string OpenApiFile = "openapi.json";

        Verify.ValidSkillName(skillDirectoryName);

        var skillDir = Path.Combine(parentDirectory, skillDirectoryName);
        Verify.DirectoryExists(skillDir);

        var openApiDocumentPath = Path.Combine(skillDir, OpenApiFile);
        if (!File.Exists(openApiDocumentPath))
        {
            throw new FileNotFoundException($"No OpenApi document for the specified path - {openApiDocumentPath} is found.");
        }

        kernel.Logger.LogTrace("Registering Rest functions from {0} OpenApi document", openApiDocumentPath);

        var skill = new Dictionary<string, ISKFunction>();

        using var stream = File.OpenRead(openApiDocumentPath);

        return await kernel.RegisterOpenApiSkillAsync(stream, skillDirectoryName, executionParameters, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Imports OpenApi document from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Name of the skill to register.</param>
    /// <param name="filePath">File path to the OpenAPI document.</param>
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("OpenApi specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenApiSkillFromFileAsync(
        this IKernel kernel,
        string skillName,
        string filePath,
        OpenApiSkillExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No OpenApi document for the specified path - {filePath} is found.");
        }

        kernel.Logger.LogTrace("Registering Rest functions from {0} OpenApi document", filePath);

        using var stream = File.OpenRead(filePath);

        return await kernel.RegisterOpenApiSkillAsync(stream, skillName, executionParameters, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Registers an OpenApi skill.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="documentStream">OpenApi document stream.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="executionParameters">Skill execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    [Obsolete("OpenApi specific extensions will be removed in a future version. Use KernelAIPluginExtensions.ImportAIPluginAsync instead")]
    public static async Task<IDictionary<string, ISKFunction>> RegisterOpenApiSkillAsync(
        this IKernel kernel,
        Stream documentStream,
        string skillName,
        OpenApiSkillExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidSkillName(skillName);

        // Parse
        var parser = new OpenApiDocumentParser(kernel.Logger);

        var operations = await parser.ParseAsync(documentStream, executionParameters?.IgnoreNonCompliantErrors ?? false, cancellationToken).ConfigureAwait(false);

        var internalHttpClient = HttpClientProvider.GetHttpClient(kernel.Config, executionParameters?.HttpClient, kernel.Logger);

        var userAgent = executionParameters?.UserAgent ?? Telemetry.HttpUserAgent;
        var runner = new RestApiOperationRunner(internalHttpClient, executionParameters?.AuthCallback, userAgent);

        var skill = new Dictionary<string, ISKFunction>();

        foreach (var operation in operations)
        {
#pragma warning disable CA1031 // Do not catch general exception types. The code will change in one of the next PRs to allow SK to throw exceptions instead of swallowing them. As a result, this suppression will be removed as well.
            try
            {
                kernel.Logger.LogTrace("Registering Rest function {0}.{1}", skillName, operation.Id);
                var function = kernel.RegisterRestApiFunction(skillName, runner, operation, executionParameters?.ServerUrlOverride, cancellationToken);
                skill[function.Name] = function;
            }
            catch (Exception ex)
            {
                //Logging the exception and keep registering other Rest functions
                kernel.Logger.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}",
                    skillName, operation.Id, ex.Message);
            }
#pragma warning restore CA1031 // Do not catch general exception types. The code will change in one of the next PRs to allow SK to throw exceptions instead of swallowing them. As a result, this suppression will be removed as well.
        }

        return skill;
    }

    #region private

    /// <summary>
    /// Registers SKFunction for a REST API operation.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="runner">The REST API operation runner.</param>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="serverUrlOverride">Optional override for REST API server URL if user input required</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>An instance of <see cref="SKFunction"/> class.</returns>
    private static ISKFunction RegisterRestApiFunction(
        this IKernel kernel,
        string skillName,
        RestApiOperationRunner runner,
        RestApiOperation operation,
        Uri? serverUrlOverride = null,
        CancellationToken cancellationToken = default)
    {
        var restOperationParameters = operation.GetParameters(serverUrlOverride);

        var logger = kernel.Logger ?? NullLogger.Instance;

        async Task<SKContext> ExecuteAsync(SKContext context)
        {
            try
            {
                // Extract function arguments from context
                var arguments = new Dictionary<string, string>();
                foreach (var parameter in restOperationParameters)
                {
                    // A try to resolve argument by alternative parameter name
                    if (!string.IsNullOrEmpty(parameter.AlternativeName) && context.Variables.TryGetValue(parameter.AlternativeName!, out string? value))
                    {
                        arguments.Add(parameter.Name, value);
                        continue;
                    }

                    // A try to resolve argument by original parameter name
                    if (context.Variables.TryGetValue(parameter.Name, out value))
                    {
                        arguments.Add(parameter.Name, value);
                        continue;
                    }

                    if (parameter.IsRequired)
                    {
                        throw new KeyNotFoundException(
                            $"No variable found in context to use as an argument for the '{parameter.Name}' parameter of the '{skillName}.{operation.Id}' Rest function.");
                    }
                }

                var result = await runner.RunAsync(operation, arguments, cancellationToken).ConfigureAwait(false);
                if (result != null)
                {
                    context.Variables.Update(result.ToString());
                }
            }
            catch (Exception ex)
            {
                logger.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}", skillName, operation.Id,
                    ex.Message);
                throw;
            }

            return context;
        }

        var parameters = restOperationParameters
            .Select(p => new ParameterView
            {
                Name = p.AlternativeName ?? p.Name,
                Description = $"{p.Description ?? p.Name}{(p.IsRequired ? " (required)" : string.Empty)}",
                DefaultValue = p.DefaultValue
            })
            .ToList();

        var function = SKFunction.FromNativeFunction(
            nativeFunction: ExecuteAsync,
            parameters: parameters,
            description: operation.Description,
            skillName: skillName,
            functionName: ConvertOperationIdToValidFunctionName(operation.Id, logger),
            logger: logger);

        return kernel.RegisterCustomFunction(function);
    }

    /// <summary>
    /// Converts operation id to valid SK Function name.
    /// A function name can contain only ASCII letters, digits, and underscores.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="logger">The logger.</param>
    /// <returns>Valid SK Function name.</returns>
    private static string ConvertOperationIdToValidFunctionName(string operationId, ILogger logger)
    {
        try
        {
            Verify.ValidFunctionName(operationId);
            return operationId;
        }
        catch (SKException)
        {
        }

        // Tokenize operation id on forward and back slashes
        string[] tokens = operationId.Split('/', '\\');
        string result = string.Empty;

        foreach (string token in tokens)
        {
            // Removes all characters that are not ASCII letters, digits, and underscores.
            string formattedToken = s_removeInvalidCharsRegex.Replace(token, "");
            result += CultureInfo.CurrentCulture.TextInfo.ToTitleCase(formattedToken.ToLower(CultureInfo.CurrentCulture));
        }

        logger.LogDebug("Operation name \"{0}\" converted to \"{1}\" to comply with SK Function name requirements. Use \"{2}\" when invoking function.", operationId, result, result);

        return result;
    }

    /// <summary>
    /// Used to convert operationId to SK function names.
    /// </summary>
    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z_]");

    #endregion
}
