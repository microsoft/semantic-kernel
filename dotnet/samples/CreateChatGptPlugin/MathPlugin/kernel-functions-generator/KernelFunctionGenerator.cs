// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace Plugins.AzureFunctions.Generator;

/// <summary>
/// Generates kernel functions
/// </summary>
[Generator]
public class KernelFunctionGenerator : ISourceGenerator
{
    /// <summary>
    /// Generates kernel functions
    /// </summary>
    public void Execute(GeneratorExecutionContext context)
    {
        var functionDetailsByPlugin = new Dictionary<string, List<FunctionDetails>>();

        foreach (var syntaxTree in context.Compilation.SyntaxTrees)
        {
            var semanticModel = context.Compilation.GetSemanticModel(syntaxTree);
            var root = syntaxTree.GetRoot();

            var configureServicesCalls = root.DescendantNodes()
                .OfType<InvocationExpressionSyntax>()
                .Where(ies => ies.Expression is MemberAccessExpressionSyntax maes && maes.Name.ToString() == "AddTransient");

            foreach (var configureServicesCall in configureServicesCalls)
            {
                // Analyze within ConfigureServices
                foreach (var invocation in configureServicesCall.DescendantNodes().OfType<InvocationExpressionSyntax>())
                {
                    var symbol = semanticModel.GetSymbolInfo(invocation).Symbol as IMethodSymbol;
                    if (symbol?.ContainingType.ToString() == "Microsoft.SemanticKernel.KernelExtensions")
                    {
                        INamedTypeSymbol? pluginTypeArgument = null;
                        if (symbol.Name == "AddFromType")
                        {
                            pluginTypeArgument = symbol.TypeArguments.FirstOrDefault() as INamedTypeSymbol;
                        }
                        else if (symbol.Name == "AddFromObject")
                        {
                            var objectCreationExpression = invocation.ArgumentList.Arguments.FirstOrDefault()?.Expression as ObjectCreationExpressionSyntax;
                            if (objectCreationExpression != null)
                            {
                                var typeInfo = semanticModel.GetTypeInfo(objectCreationExpression);
                                pluginTypeArgument = typeInfo.Type as INamedTypeSymbol;
                            }
                        }

                        if (pluginTypeArgument != null && configureServicesCall.Expression is MemberAccessExpressionSyntax maes)
                        {
                            var pluginName = pluginTypeArgument.Name;
                            var functionDetails = this.ExtractFunctionDetails(context, pluginTypeArgument);
                            functionDetailsByPlugin[pluginName] = functionDetails;
                        }
                    }
                }
            }
        }

        // Generate source for each plugin
        foreach (var pluginEntry in functionDetailsByPlugin)
        {
            var sourceCode = GenerateClassSource("AzureFunctionPlugins", pluginEntry.Key, pluginEntry.Value);
            context.AddSource($"{pluginEntry.Key}.g.cs", sourceCode);
        }
    }

    private List<FunctionDetails> ExtractFunctionDetails(GeneratorExecutionContext context, INamedTypeSymbol pluginClass)
    {
        var functionDetailsList = new List<FunctionDetails>();

        foreach (var member in pluginClass.GetMembers())
        {
            if (member is IMethodSymbol methodSymbol && methodSymbol.GetAttributes().Any(attr => attr?.AttributeClass?.Name == "KernelFunctionAttribute"))
            {
                var functionDetails = new FunctionDetails
                {
                    Name = methodSymbol.Name,
                    Description = methodSymbol.GetAttributes().FirstOrDefault(a => a?.AttributeClass?.Name == "DescriptionAttribute")?.ConstructorArguments.FirstOrDefault().Value.ToString(),
                    Parameters = new List<ParameterDetails>()
                };

                foreach (var parameter in methodSymbol.Parameters)
                {
                    var parameterDetails = new ParameterDetails
                    {
                        Name = parameter.Name,
                        Type = parameter.Type.ToString(),
                        Description = parameter.GetAttributes().FirstOrDefault(a => a?.AttributeClass?.Name == "DescriptionAttribute")?.ConstructorArguments.FirstOrDefault().Value.ToString()
                    };

                    functionDetails.Parameters.Add(parameterDetails);
                }

                functionDetailsList.Add(functionDetails);
            }
        }

        return functionDetailsList;
    }

    // Generate the source code for a folder of prompts
    private static string GenerateClassSource(string rootNamespace, string pluginName, List<FunctionDetails> functions)
    {
        StringBuilder functionsCode = new();

        foreach (var function in functions)
        {
            functionsCode.AppendLine(GenerateFunctionSource(pluginName, function) ?? string.Empty);
        }

        return $@"/* ### GENERATED CODE - Do not modify. Edits will be lost on build. ### */
    using System;
    using System.Net;
    using System.Reflection;
    using System.Threading.Tasks;
    using Microsoft.Azure.Functions.Worker;
    using Microsoft.Azure.Functions.Worker.Http;
    using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;
    using Microsoft.Extensions.Logging;
    using Microsoft.OpenApi.Models;
    using Microsoft.SemanticKernel;
    using Plugins.AzureFunctions.Extensions;

    namespace {rootNamespace};

    public class {pluginName}
    {{
        private readonly ILogger _logger;
        private readonly AIPluginRunner _pluginRunner;

        public {pluginName}(AIPluginRunner pluginRunner, ILoggerFactory loggerFactory)
        {{
            _pluginRunner = pluginRunner;
            _logger = loggerFactory.CreateLogger<{pluginName}>();
        }}

        {functionsCode}
    }}";
    }

    private static string? GenerateFunctionSource(string pluginName, FunctionDetails functionDetails)
    {
        string modelClassName = $"{functionDetails.Name}Model"; // Name of the model class
        string parameterAttributes = GenerateModelClassSource(modelClassName, functionDetails.Parameters);

        return $@"
        {parameterAttributes}

        [OpenApiOperation(operationId: ""{functionDetails.Name}"", tags: new[] {{ ""{functionDetails.Name}"" }})]
        [OpenApiRequestBody(contentType: ""application/json"", bodyType: typeof({modelClassName}), Required = true, Description = ""JSON request body"")]
        [OpenApiResponseWithBody(statusCode: HttpStatusCode.OK, contentType: ""application/json"", bodyType: typeof(string), Description = ""The OK response"")]
        [Function(""{functionDetails.Name}"")]
        public async Task<HttpResponseData> {functionDetails.Name}([HttpTrigger(AuthorizationLevel.Anonymous, ""post"")] HttpRequestData req)
        {{
            _logger.LogInformation(""HTTP trigger processed a request for function {pluginName}-{functionDetails.Name}."");
            return await _pluginRunner.RunAIPluginOperationAsync<{modelClassName}>(req, ""{pluginName}"", ""{functionDetails.Name}"");
        }}";
    }

    private static string GenerateModelClassSource(string modelClassName, List<ParameterDetails> parameters)
    {
        StringBuilder modelClassBuilder = new();

        modelClassBuilder.AppendLine($"public class {modelClassName}");
        modelClassBuilder.AppendLine("{");

        foreach (var parameter in parameters)
        {
            modelClassBuilder.AppendLine($"    public {parameter.Type} {parameter.Name} {{ get; set; }}");
        }

        modelClassBuilder.AppendLine("}");

        return modelClassBuilder.ToString();
    }

    /// <summary>
    /// Does nothing
    /// </summary>
    public void Initialize(GeneratorInitializationContext context)
    {
        // No initialization required
    }
}

/// <summary>
/// Function details
/// </summary>
public class FunctionDetails
{
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public List<ParameterDetails> Parameters { get; set; } = new List<ParameterDetails>();
}

/// <summary>
/// Parameter details
/// </summary>
public class ParameterDetails
{
    public string Name { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
}
