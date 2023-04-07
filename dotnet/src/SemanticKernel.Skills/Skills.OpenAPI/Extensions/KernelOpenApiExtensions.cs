// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Resources;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;
using Microsoft.SemanticKernel.Skills.OpenAPI.Rest;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;

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
    /// <param name="httpClient">Optional HttpClient to use for the request.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenApiSkillFromUrlAsync(
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

            Stream stream = await response.Content.ReadAsStreamAsync();
            if (stream == null)
            {
                throw new MissingManifestResourceException($"Unable to load OpenApi skill from url '{url}'.");
            }

            return kernel.RegisterOpenApiSkill(stream, skillName, authCallback);
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
    /// Imports OpenApi document from assembly resource.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> ImportOpenApiSkillFromResource(this IKernel kernel, string skillName,
        AuthenticateRequestAsyncCallback? authCallback = null)
    {
        Verify.ValidSkillName(skillName);

        var type = typeof(SkillResourceNames);

        var resourceName = $"{skillName}.openapi.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName); //TODO: support yaml resources
        if (stream == null)
        {
            throw new MissingManifestResourceException($"Unable to load OpenApi skill from assembly resource '{resourceName}'.");
        }

        return kernel.RegisterOpenApiSkill(stream, skillName, authCallback);
    }

    /// <summary>
    /// Imports OpenApi document from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the skill directory.</param>
    /// <param name="skillDirectoryName">Name of the directory containing the selected skill.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> ImportOpenApiSkillFromDirectory(
        this IKernel kernel, string parentDirectory, string skillDirectoryName, AuthenticateRequestAsyncCallback? authCallback = null)
    {
        const string OPENAPI_FILE = "openapi.json";

        Verify.ValidSkillName(skillDirectoryName);

        var skillDir = Path.Join(parentDirectory, skillDirectoryName);
        Verify.DirectoryExists(skillDir);

        var openApiDocumentPath = Path.Join(skillDir, OPENAPI_FILE);
        if (!File.Exists(openApiDocumentPath))
        {
            throw new FileNotFoundException($"No OpenApi document for the specified path - {openApiDocumentPath} is found.");
        }

        kernel.Log.LogTrace("Registering Rest functions from {0} OpenApi document.", openApiDocumentPath);

        var skill = new Dictionary<string, ISKFunction>();

        using var stream = File.OpenRead(openApiDocumentPath);

        return kernel.RegisterOpenApiSkill(stream, skillDirectoryName, authCallback);
    }

    /// <summary>
    /// Imports OpenApi document from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Name of the skill to register.</param>
    /// <param name="filePath">File path to the OpenAPI document.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> ImportOpenApiSkillFromFile(this IKernel kernel, string skillName, string filePath,
        AuthenticateRequestAsyncCallback? authCallback = null)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No OpenApi document for the specified path - {filePath} is found.");
        }

        kernel.Log.LogTrace("Registering Rest functions from {0} OpenApi document.", filePath);

        var skill = new Dictionary<string, ISKFunction>();

        using var stream = File.OpenRead(filePath);

        return kernel.RegisterOpenApiSkill(stream, skillName, authCallback);
    }

    /// <summary>
    /// Registers an OpenApi skill.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="documentStream">OpenApi document stream.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> RegisterOpenApiSkill(this IKernel kernel, Stream documentStream, string skillName,
        AuthenticateRequestAsyncCallback? authCallback = null)
    {
        Verify.NotNull(kernel, nameof(kernel));
        Verify.ValidSkillName(skillName);

        //Parse
        var parser = new OpenApiDocumentParser();

        var operations = parser.Parse(documentStream);

        var skill = new Dictionary<string, ISKFunction>();

        foreach (var operation in operations)
        {
            try
            {
                kernel.Log.LogTrace("Registering Rest function {0}.{1}.", skillName, operation.Id);
                var function = kernel.RegisterRestApiFunction(skillName, operation, authCallback);
                skill[function.Name] = function;
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                //Logging the exception and keep registering other Rest functions
                kernel.Log.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}", skillName, operation.Id,
                    ex.Message);
            }
        }

        return skill;
    }

    #region private

    /// <summary>
    /// Registers SKFunction for a REST API operation.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <returns>An instance of <see cref="SKFunction"/> class.</returns>
    private static ISKFunction RegisterRestApiFunction(this IKernel kernel, string skillName, RestApiOperation operation,
        AuthenticateRequestAsyncCallback? authCallback = null)
    {
        var restOperationParameters = operation.GetParameters();

        async Task<SKContext> ExecuteAsync(SKContext context)
        {
            try
            {
                var runner = new RestApiOperationRunner(new HttpClient(), authCallback);

                //Extract function arguments from context
                var arguments = new Dictionary<string, string>();
                foreach (var parameter in restOperationParameters)
                {
                    //A try to resolve argument by alternative parameter name
                    if (!string.IsNullOrEmpty(parameter.AlternativeName) && context.Variables.Get(parameter.AlternativeName, out var value))
                    {
                        arguments.Add(parameter.Name, value);
                        continue;
                    }

                    //A try to resolve argument by original parameter name
                    if (context.Variables.Get(parameter.Name, out value))
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

                var result = await runner.RunAsync(operation, arguments, context.CancellationToken);
                if (result != null)
                {
                    context.Variables.Update(result.ToString());
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                kernel.Log.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}", skillName, operation.Id,
                    ex.Message);
                context.Fail(ex.Message, ex);
            }

            return context;
        }

        //TODO: to be fixed later
#pragma warning disable CA2000 // Dispose objects before losing scope.
        var function = new SKFunction(
            delegateType: SKFunction.DelegateTypes.ContextSwitchInSKContextOutTaskSKContext,
            delegateFunction: ExecuteAsync,
            parameters: restOperationParameters.Select(p => new ParameterView()
            { Name = p.AlternativeName ?? p.Name, Description = p.Name, DefaultValue = p.DefaultValue ?? string.Empty })
                .ToList(), //functionConfig.PromptTemplate.GetParameters(),
            description: operation.Description,
            skillName: skillName,
            functionName: operation.Id,
            isSemantic: false,
            log: kernel.Log);
#pragma warning restore CA2000 // Dispose objects before losing scope

        return kernel.RegisterCustomFunction(skillName, function);
    }

    #endregion
}
