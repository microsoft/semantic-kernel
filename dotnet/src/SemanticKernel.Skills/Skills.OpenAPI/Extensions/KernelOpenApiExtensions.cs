// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Resources;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;
using RestSkills;
using RestSkills.Authentication;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;

/// <summary>
/// Class for extensions methods for IKernel interface.
/// </summary>
public static class KernelOpenApiExtensions
{
    /// <summary>
    /// Imports OpenApi document from assembly resource.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="skillName">Skill name.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> ImportOpenApiSkillFromResource(this IKernel kernel, string skillName)
    {
        Verify.ValidSkillName(skillName);

        var type = typeof(SkillResourceNames);

        var resourceName = $"{skillName}.openapi.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName); //TODO: support yaml resources
        if (stream == null)
        {
            throw new MissingManifestResourceException($"Unable to load OpenApi skill from assembly resource '{resourceName}'.");
        }

        return kernel.RegisterOpenApiSkill(stream, skillName);
    }

    /// <summary>
    /// Imports OpenApi document from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the skill directory.</param>
    /// <param name="skillDirectoryName">Name of the directory containing the selected skill.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> ImportOpenApiSkillFromDirectory(this IKernel kernel, string parentDirectory, string skillDirectoryName)
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

        return kernel.RegisterOpenApiSkill(stream, skillDirectoryName);
    }

    /// <summary>
    /// Registers an OpenApi skill.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="documentStream">OpenApi document stream.</param>
    /// <param name="skillName">Skill name.</param>
    /// <returns>A list of all the semantic functions representing the skill.</returns>
    public static IDictionary<string, ISKFunction> RegisterOpenApiSkill(this IKernel kernel, Stream documentStream, string skillName)
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
                skill[skillName] = kernel.RegisterRestFunction(skillName, operation);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                //Logging the exception and keep registering other Rest functions
                kernel.Log.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}", skillName, operation.Id, ex.Message);
            }
        }

        return skill;
    }

    #region private
    private static ISKFunction RegisterRestFunction(this IKernel kernel, string skillName, RestApiOperation operation)
    {
        var restOperationParameters = operation.GetParameters();

        async Task<SKContext> ExecuteAsync(SKContext context)
        {
            try
            {
                var runner = new RestApiOperationRunner(new HttpClient(), new BearerTokenHandler());

                //Extract function arguments from context
                var arguments = new Dictionary<string, string>();
                foreach (var parameter in restOperationParameters)
                {
                    if (context.Variables.Get(parameter.Name, out var value))
                    {
                        arguments.Add(parameter.Name, value);
                        continue;
                    }

                    if (parameter.IsRequired)
                    {
                        throw new KeyNotFoundException($"No variable found in context to use as an argument for the '{parameter.Name}' of the '{skillName}.{operation.Id}' Rest function.");
                    }
                }

                //Create payload. It's a workaround that should be removed when payload is automatically created by RestOperation class
                var payload = default(JsonNode);
                if (context.Variables.Get("body", out var body))
                {
                    payload = JsonValue.Parse(body);
                }

                var result = await runner.RunAsync(operation, arguments, payload, context.CancellationToken);
                if (result != null)
                {
                    context.Variables.Update(result.ToString());
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                kernel.Log.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}", skillName, operation.Id, ex.Message);
                context.Fail(ex.Message, ex);
            }

            return context;
        }

        //Temporary workaround to advertize the 'value' parameter
        //restOperation.Parameters.Add(new RestParameter() { Location = RestParameterLocation.Body, IsRequired = true, Name = "value" });

        //TODO: to be fixed later
#pragma warning disable CA2000 // Dispose objects before losing scope.
        var function = new SKFunction(
            delegateType: SKFunction.DelegateTypes.ContextSwitchInSKContextOutTaskSKContext,
            delegateFunction: ExecuteAsync,
            parameters: restOperationParameters.Select(p => new ParameterView() { Name = p.Name, Description = p.Name, DefaultValue = p.DefaultValue }).ToList(), //functionConfig.PromptTemplate.GetParameters(),
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
