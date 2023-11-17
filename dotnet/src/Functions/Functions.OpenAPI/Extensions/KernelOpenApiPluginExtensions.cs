// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenApi;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;

/// <summary>
/// Provides extension methods for importing plugins exposed as OpenAPI v3 endpoints.
/// </summary>
public static class KernelOpenApiPluginExtensions
{
    /// <summary>
    /// Imports a plugin that is exposed as an OpenAPI v3 endpoint.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="filePath">The file path to the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenApiPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, executionParameters?.HttpClient, kernel.LoggerFactory);
#pragma warning restore CA2000

        var openApiSpec = await DocumentLoader.LoadDocumentFromFilePathAsync(
            filePath,
            kernel.LoggerFactory.CreateLogger(typeof(KernelOpenApiPluginExtensions)),
            cancellationToken).ConfigureAwait(false);

        return await RegisterOpenApiPluginAsync(
            kernel,
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Imports a plugin that is exposed as an OpenAPI v3 endpoint.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="uri">A local or remote URI referencing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenApiPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        Uri uri,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, executionParameters?.HttpClient, kernel.LoggerFactory);
#pragma warning restore CA2000

        var openApiSpec = await DocumentLoader.LoadDocumentFromUriAsync(
            uri,
            kernel.LoggerFactory.CreateLogger(typeof(KernelOpenApiPluginExtensions)),
            httpClient,
            executionParameters?.AuthCallback,
            executionParameters?.UserAgent,
            cancellationToken).ConfigureAwait(false);

        return await RegisterOpenApiPluginAsync(
            kernel,
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            uri,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Imports a plugin that is exposed as an OpenAPI v3 endpoint.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="stream">A stream representing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenApiPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        Stream stream,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, executionParameters?.HttpClient, kernel.LoggerFactory);
#pragma warning restore CA2000

        var openApiSpec = await DocumentLoader.LoadDocumentFromStreamAsync(stream).ConfigureAwait(false);

        return await RegisterOpenApiPluginAsync(
            kernel,
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    #region private

    private static async Task<IDictionary<string, ISKFunction>> RegisterOpenApiPluginAsync(
        IKernel kernel,
        string pluginName,
        OpenApiFunctionExecutionParameters? executionParameters,
        HttpClient httpClient,
        string pluginJson,
        Uri? documentUri = null,
        CancellationToken cancellationToken = default)
    {
        var parser = new OpenApiDocumentParser(kernel.LoggerFactory);

        using (var documentStream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(pluginJson)))
        {
            var operations = await parser.ParseAsync(
                documentStream,
                executionParameters?.IgnoreNonCompliantErrors ?? false,
                executionParameters?.OperationsToExclude,
                cancellationToken).ConfigureAwait(false);

            var runner = new RestApiOperationRunner(
                httpClient,
                executionParameters?.AuthCallback,
                executionParameters?.UserAgent,
                executionParameters?.EnableDynamicPayload ?? false,
                executionParameters?.EnablePayloadNamespacing ?? false);

            var plugin = new Dictionary<string, ISKFunction>();

            ILogger logger = kernel.LoggerFactory.CreateLogger(typeof(KernelOpenApiPluginExtensions));
            foreach (var operation in operations)
            {
                try
                {
                    logger.LogTrace("Registering Rest function {0}.{1}", pluginName, operation.Id);
                    var function = kernel.RegisterRestApiFunction(pluginName, runner, operation, executionParameters, documentUri, cancellationToken);
                    plugin[function.Name] = function;
                }
                catch (Exception ex) when (!ex.IsCriticalException())
                {
                    //Logging the exception and keep registering other Rest functions
                    logger.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}",
                        pluginName, operation.Id, ex.Message);
                }
            }

            return plugin;
        }
    }

    /// <summary>
    /// Registers SKFunction for a REST API operation.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="runner">The REST API operation runner.</param>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="executionParameters">Function execution parameters.</param>
    /// <param name="documentUri">The URI of OpenApi document.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>An instance of <see cref="SKFunction"/> class.</returns>
    private static ISKFunction RegisterRestApiFunction(
        this IKernel kernel,
        string pluginName,
        RestApiOperationRunner runner,
        RestApiOperation operation,
        OpenApiFunctionExecutionParameters? executionParameters,
        Uri? documentUri = null,
        CancellationToken cancellationToken = default)
    {
        var restOperationParameters = operation.GetParameters(
            executionParameters?.EnableDynamicPayload ?? false,
            executionParameters?.EnablePayloadNamespacing ?? false
        );

        var logger = kernel.LoggerFactory is not null ? kernel.LoggerFactory.CreateLogger(typeof(KernelOpenApiPluginExtensions)) : NullLogger.Instance;

        async Task<RestApiOperationResponse> ExecuteAsync(SKContext context)
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
                            $"No variable found in context to use as an argument for the '{parameter.Name}' parameter of the '{pluginName}.{operation.Id}' Rest function.");
                    }
                }

                var options = new RestApiOperationRunOptions
                {
                    ServerUrlOverride = executionParameters?.ServerUrlOverride,
                    ApiHostUrl = documentUri is not null ? new Uri(documentUri.GetLeftPart(UriPartial.Authority)) : null
                };

                return await runner.RunAsync(operation, arguments, options, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                logger.LogError(ex, "RestAPI function {Plugin}.{Name} execution failed with error {Error}", pluginName, operation.Id, ex.Message);
                throw;
            }
        }

        var parameters = restOperationParameters
            .Select(p => new ParameterView(p.AlternativeName ?? p.Name)
            {
                Description = $"{p.Description ?? p.Name}{(p.IsRequired ? " (required)" : string.Empty)}",
                DefaultValue = p.DefaultValue ?? string.Empty,
                Type = string.IsNullOrEmpty(p.Type) ? null : new ParameterViewType(p.Type),
                IsRequired = p.IsRequired,
                Schema = p.Schema,
            })
            .ToList();

        var returnParameter = operation.GetDefaultReturnParameter();

        var function = SKFunction.Create(
            method: ExecuteAsync,
            parameters: parameters,
            returnParameter: returnParameter,
            description: operation.Description,
            pluginName: pluginName,
            functionName: ConvertOperationIdToValidFunctionName(operation.Id, logger),
            loggerFactory: kernel.LoggerFactory);

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

        logger.LogInformation("Operation name \"{0}\" converted to \"{1}\" to comply with SK Function name requirements. Use \"{2}\" when invoking function.", operationId, result, result);

        return result;
    }

    /// <summary>
    /// Used to convert operationId to SK function names.
    /// </summary>
    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z_]");

    #endregion
}
