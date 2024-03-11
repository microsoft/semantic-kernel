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
            if (promptFile != default && configFile != default)
            {
                functionsCode.AppendLine(GenerateFunctionSource(skillName, promptFile, configFile) ?? string.Empty);
            }
        }

        string aiPluginEndpointCode = GenerateAIPluginEndpointCode(skillName);

        return $@"/* ### GENERATED CODE - Do not modify. Edits will be lost on build. ### */
using System;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;
using AIPlugins.AzureFunctions.Extensions;

namespace {rootNamespace};

public class {skillName}
{{
    private readonly ILogger _logger;
    private readonly IAIPluginRunner _pluginRunner;

    public {skillName}(IAIPluginRunner pluginRunner, ILoggerFactory loggerFactory)
    {{
        this._pluginRunner = pluginRunner;
        this._logger = loggerFactory.CreateLogger<{skillName}>();
    }}

    {aiPluginEndpointCode}
    {functionsCode}
}}";
    }

    private static string GenerateAIPluginEndpointCode(string skillName)
    {
        string skillDescription = $"API for {skillName}";
        return $@"[Function(""{skillName}/.well-known/ai-plugin.json"")]
    [OpenApiIgnore]
    public Task<HttpResponseData> GetAIPluginSpecAsync([HttpTrigger(AuthorizationLevel.Anonymous, ""get"")] HttpRequestData req)
    {{
        this._logger.LogInformation(""HTTP trigger processed a request for function GetAIPluginSpecAsync."");
        return AIPluginHelpers.GenerateAIPluginJsonResponseAsync(req, ""{skillName}"", ""{skillDescription}"", ""{skillDescription}"");
    }}";
    }

    private static string? GenerateFunctionSource(string skillName, AdditionalText promptFile, AdditionalText configFile)
    {
        // Get the function name from the directory name
        string? functionName = Path.GetFileName(Path.GetDirectoryName(promptFile.Path));
        if (string.IsNullOrWhiteSpace(functionName)) { return null; }

        string? metadataJson = configFile.GetText()?.ToString();
        if (string.IsNullOrWhiteSpace(metadataJson)) { return null; }

        // Get the function description from the config file
        PromptConfig? config = JsonConvert.DeserializeObject<PromptConfig>(metadataJson!);
        if (config == null) { return null; }

        string descriptionProperty = string.IsNullOrWhiteSpace(config.Description)
            ? string.Empty
            : $@", Description = ""{config.Description}""";

        string parameterAttributes = GenerateParameterAttributesSource(config.Input?.Parameters);

        return $@"
    [Function(""{skillName}/{functionName}"")]
    [OpenApiOperation(operationId: ""{functionName}"", tags: new[] {{ ""{skillName}"", ""{functionName}"" }}{descriptionProperty})]{parameterAttributes}
    [OpenApiResponseWithBody(statusCode: HttpStatusCode.OK, contentType: ""text/plain"", bodyType: typeof(string), Description = ""The OK response"")]
    public Task<HttpResponseData> {functionName}Async([HttpTrigger(AuthorizationLevel.Anonymous, ""post"")] HttpRequestData req)
    {{
        this._logger.LogInformation(""HTTP trigger processed a request for function {functionName}."");
        return this._pluginRunner.RunAIPluginOperationAsync(req, ""{skillName}/{functionName}"");
    }}";
    }

    private static string GenerateParameterAttributesSource(
        List<PromptConfig.ParameterConfig>? parameters)
    {
        string inputDescription = string.Empty;
        StringBuilder parameterStringBuilder = new();

        if (parameters != null)
        {
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
        }

        parameterStringBuilder.AppendLine();
        parameterStringBuilder.Append($@"    [OpenApiRequestBody(""text/plain"", typeof(string){inputDescription})]");

        return parameterStringBuilder.ToString();
    }

    public void Initialize(GeneratorInitializationContext context)
    {
        // No initialization required
    }
}
