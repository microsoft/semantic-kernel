// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using AIPlugins.AzureFunctions.Generator.Extensions;
using AIPlugins.AzureFunctions.Generator.Models;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Text;
using Newtonsoft.Json;

namespace AIPlugins.AzureFunctions.Generator;

[Generator]
public class SemanticSkillGenerator : ISourceGenerator
{
    private const string DefaultSkillNamespace = "AIPlugins";
    private const string FunctionConfigFilename = "config.json";
    private const string FunctionPromptFilename = "skprompt.txt";

    public void Execute(GeneratorExecutionContext context)
    {
        var rootNamespace = context.GetRootNamespace() ?? DefaultSkillNamespace;

        // Get the additional files that represent the skills and functions
        var skillFiles = context.AdditionalFiles.Where(f =>
            f.Path.Contains(FunctionConfigFilename) ||
            f.Path.Contains(FunctionPromptFilename));

        // Group first by function name, then by skill name
        var fnFileGroup = skillFiles.GroupBy(f => Path.GetDirectoryName(f.Path));

        // Group the files by skill name
        var skillGroups = fnFileGroup.GroupBy(f => Path.GetFileName(Path.GetDirectoryName(f.Key)));

        // Generate a class for each skill
        foreach (var skillGroup in skillGroups)
        {
            string? skillName = skillGroup.Key;
            if (string.IsNullOrWhiteSpace(skillName))
            {
                continue;
            }
            
            string classSource = GenerateClassSource(rootNamespace, skillName, skillGroup);
            context.AddSource(skillName, SourceText.From(classSource, Encoding.UTF8));
        }
    }

    // Generate the source code for a skill class
    private static string GenerateClassSource(string rootNamespace, string skillName, IGrouping<string, IGrouping<string, AdditionalText>> skillGroup)
    {
        // Use a StringBuilder to build the class source
        StringBuilder functionsCode = new();

        foreach (var functionGroup in skillGroup)
        {
            // Get the "skprompt.txt" and "config.json" files for this function
            AdditionalText? configFile = functionGroup.FirstOrDefault(f => Path.GetFileName(f.Path).Equals(FunctionConfigFilename, StringComparison.InvariantCultureIgnoreCase));
            AdditionalText? promptFile = functionGroup.FirstOrDefault(f => Path.GetFileName(f.Path).Equals(FunctionPromptFilename, StringComparison.InvariantCultureIgnoreCase));
            if (promptFile == default || configFile == default)
            {
                continue;
            }

            // Get the function name from the directory name
            string? functionName = Path.GetFileName(Path.GetDirectoryName(promptFile.Path));
            if (string.IsNullOrWhiteSpace(functionName)) { continue; }

            string? metadataJson = configFile.GetText()?.ToString();
            if (string.IsNullOrWhiteSpace(metadataJson)) { continue; }

            // Get the function description from the config file
            PromptConfig? config = JsonConvert.DeserializeObject<PromptConfig>(metadataJson!);
            if (config == null) { continue; }

            string functionSource = GenerateFunctionSource(
                skillName,
                functionName,
                config?.Description ?? string.Empty,
                config?.Input?.Parameters);
            if (string.IsNullOrWhiteSpace(functionSource)) { continue; }

            functionsCode.AppendLine(functionSource);
        }
        
        AIPluginModel aiPlugin = new()
        {
            SchemaVersion = "1.0",
            NameForModel = skillName,
            NameForHuman = skillName,
            DescriptionForModel = $"API for {skillName}",
            DescriptionForHuman = $"API for {skillName}",
            Api = new()
            {
                Url = "INSERT_SKILL_OPENAPI_PATH"
            }
        };

        string aiPluginJson = JsonConvert.SerializeObject(aiPlugin, Formatting.Indented)
            .Replace(@"""", @"""""");

        string classSource = $@"/* ### GENERATED CODE - Do not modify. Edits will be lost on build. ### */
using System;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.OpenApi.Models;
using {rootNamespace}.Extensions;

namespace {rootNamespace};

public class {skillName}
{{
    private readonly ILogger _logger;

    public {skillName}(ILoggerFactory loggerFactory)
    {{
        this._logger = loggerFactory.CreateLogger<{skillName}>();
    }}

    [Function(""{skillName}/.well-known/ai-plugin.json"")]
    public async Task<HttpResponseData> GetAIPluginSpecAsync([HttpTrigger(AuthorizationLevel.Anonymous, ""get"")] HttpRequestData req)
    {{
        const string aiPluginJson = @""{aiPluginJson}"";

        this._logger.LogInformation(""HTTP trigger processed a request for function GetAIPluginSpecAsync."");

        string skillUri = req.Url.GetLeftPart(UriPartial.Path);
        skillUri = skillUri.Remove(skillUri.IndexOf(""skill/.well-known"", StringComparison.InvariantCultureIgnoreCase));
        Uri openApiSpecUri = new(baseUri: new(skillUri), $""swagger.json?tag={skillName}"");

        var response = req.CreateResponse(HttpStatusCode.OK);
        response.Headers.Add(""Content-Type"", ""application/json; charset=utf-8"");
        await response.WriteStringAsync(aiPluginJson.Replace(""{aiPlugin.Api.Url}"", openApiSpecUri.ToString()));
        await Task.CompletedTask;
        return response;
    }}

    {functionsCode}
}}";

        return classSource;
    }

    // Generate the source code for a function
    private static string GenerateFunctionSource(string skillName, string functionName, string functionDescription, List<PromptConfig.ParameterConfig>? parameters)
    {
        string descriptionProperty = string.IsNullOrWhiteSpace(functionDescription)
            ? string.Empty
            : $@", Description = ""{functionDescription}""";

        string inputDescription = string.Empty;
        string parameterAttributes = string.Empty;
        if (parameters != null && parameters.Any())
        {
            StringBuilder parameterStringBuilder = new();
            foreach (var parameter in parameters)
            {
                if (parameter.Name.Equals("input", StringComparison.InvariantCultureIgnoreCase))
                {
                    // "input" is a special parameter that is handled differently. It must be added as
                    // the body attribute.
                    if (!string.IsNullOrWhiteSpace(parameter.Description))
                    {
                        inputDescription = $@", Description = ""{parameter.Description}""";
                    }

                    continue;
                }

                parameterStringBuilder.AppendLine(); // Start with a newline
                parameterStringBuilder.Append($@"    [OpenApiParameter(name: ""{parameter.Name}""");

                if (!string.IsNullOrWhiteSpace(parameter.Description))
                {
                    parameterStringBuilder.Append($@", Description = ""{parameter.Description}""");
                }
                
                parameterStringBuilder.Append(", In = ParameterLocation.Query");

                parameterStringBuilder.Append(", Type = typeof(string))]");
            }
            
            parameterAttributes = parameterStringBuilder.ToString();
        }

        return $@"
    [Function(""{skillName}/{functionName}"")]
    [OpenApiOperation(operationId: ""{functionName}"", tags: new[] {{ ""{skillName}"", ""{functionName}"" }}{descriptionProperty})]
    [OpenApiRequestBody(""application/json"", typeof(string){inputDescription})]
    [OpenApiResponseWithBody(statusCode: HttpStatusCode.OK, contentType: ""text/plain"", bodyType: typeof(string), Description = ""The OK response"")]{parameterAttributes}
    public async Task<HttpResponseData> {functionName}Async([HttpTrigger(AuthorizationLevel.Anonymous, ""post"")] HttpRequestData req)
    {{
        this._logger.LogInformation(""HTTP trigger processed a request for function {functionName}."");

        ContextVariables contextVariables = KernelHelpers.LoadContextVariablesFromRequest(req);

        IKernel kernel = KernelHelpers.CreateKernel(this._logger);
        var function = kernel.Skills.GetFunction(""{skillName}"", ""{functionName}"");
        var result = await kernel.RunAsync(contextVariables, function);
        if (result.ErrorOccurred)
        {{
            return await req.CreateResponseWithMessageAsync(HttpStatusCode.BadRequest, result.LastErrorDescription);
        }}

        var response = req.CreateResponse(HttpStatusCode.OK);
        response.Headers.Add(""Content-Type"", ""text/plain; charset=utf-8"");
        await response.WriteStringAsync(result.Result);
        return response;
    }}";
    }

    public void Initialize(GeneratorInitializationContext context)
    {
        // No initialization required
    }
}
