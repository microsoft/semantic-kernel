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
public class SemanticFunctionGenerator : ISourceGenerator
{
    private const string DefaultFunctionNamespace = "AIPlugins";
    private const string FunctionConfigFilename = "config.json";
    private const string FunctionPromptFilename = "skprompt.txt";

    public void Execute(GeneratorExecutionContext context)
    {
        var rootNamespace = context.GetRootNamespace();

        if (String.IsNullOrEmpty(rootNamespace))
        {
            rootNamespace = DefaultFunctionNamespace;
        }

        // Get the additional files that represent the functions and functions
        var functionFiles = context.AdditionalFiles.Where(f =>
            f.Path.Contains(FunctionConfigFilename) ||
            f.Path.Contains(FunctionPromptFilename));

        // Group first by function name, then by parent folder
        var fnFileGroup = functionFiles.GroupBy(f => Path.GetDirectoryName(f.Path));

        // Group the files by parent folder name
        var folderGroups = fnFileGroup.GroupBy(f => Path.GetFileName(Path.GetDirectoryName(f.Key)));

        // Generate a class for each folder
        foreach (var folderGroup in folderGroups)
        {
            string? folderName = folderGroup.Key;
            if (string.IsNullOrWhiteSpace(folderName))
            {
                continue;
            }

            string classSource = GenerateClassSource(rootNamespace!, folderName, folderGroup);
            context.AddSource(folderName, SourceText.From(classSource, Encoding.UTF8));
        }
    }

    // Generate the source code for a folder of semantic functions
    private static string GenerateClassSource(string rootNamespace, string folderName, IGrouping<string, IGrouping<string, AdditionalText>> folderGroup)
    {
        // Use a StringBuilder to build the class source
        StringBuilder functionsCode = new();

        foreach (var functionGroup in folderGroup)
        {
            // Get the "skprompt.txt" and "config.json" files for this function
            AdditionalText? configFile = functionGroup.FirstOrDefault(f => Path.GetFileName(f.Path).Equals(FunctionConfigFilename, StringComparison.Ordinal));
            AdditionalText? promptFile = functionGroup.FirstOrDefault(f => Path.GetFileName(f.Path).Equals(FunctionPromptFilename, StringComparison.Ordinal));
            if (promptFile != default && configFile != default)
            {
                functionsCode.AppendLine(GenerateFunctionSource(promptFile, configFile) ?? string.Empty);
            }
        }

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

#pragma warning disable VSTHRD200

namespace {rootNamespace};

public class {folderName}
{{
    private readonly ILogger _logger;
    private readonly IAIPluginRunner _pluginRunner;

    public {folderName}(IAIPluginRunner pluginRunner, ILoggerFactory loggerFactory)
    {{
        this._pluginRunner = pluginRunner;
        this._logger = loggerFactory.CreateLogger<{folderName}>();
    }}

    {functionsCode}
}}";
    }

    private static string? GenerateFunctionSource(AdditionalText promptFile, AdditionalText configFile)
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
    [OpenApiOperation(operationId: ""{functionName}"", tags: new[] {{ ""ExecuteFunction"" }}{descriptionProperty})]{parameterAttributes}
    [OpenApiResponseWithBody(statusCode: HttpStatusCode.OK, contentType: ""text/plain"", bodyType: typeof(string), Description = ""The OK response"")]
    [Function(""{functionName}"")]
    public Task<HttpResponseData> Run([HttpTrigger(AuthorizationLevel.Anonymous, ""post"")] HttpRequestData req)
    {{
        this._logger.LogInformation(""HTTP trigger processed a request for function {functionName}."");
        return this._pluginRunner.RunAIPluginOperationAsync(req, ""{functionName}"");
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
                if (parameter.Name.Equals("input", StringComparison.Ordinal))
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
