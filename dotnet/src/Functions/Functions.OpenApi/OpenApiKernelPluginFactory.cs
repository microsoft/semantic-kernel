// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Provides static factory methods for creating KernelPlugins from OpenAPI specifications.
/// </summary>
public static partial class OpenApiKernelPluginFactory
{
    /// <summary>
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification.
    /// </summary>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="filePath">The file path to the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static async Task<KernelPlugin> CreateFromOpenApiAsync(
        string pluginName,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient);
#pragma warning restore CA2000

        var loggerFactory = executionParameters?.LoggerFactory;
        var logger = loggerFactory?.CreateLogger(typeof(OpenApiKernelExtensions)) ?? NullLogger.Instance;

        var openApiSpec = await DocumentLoader.LoadDocumentFromFilePathAsync(
            filePath,
            logger,
            cancellationToken).ConfigureAwait(false);

        return await CreateOpenApiPluginAsync(
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            loggerFactory: loggerFactory,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification.
    /// </summary>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="uri">A URI referencing the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static async Task<KernelPlugin> CreateFromOpenApiAsync(
        string pluginName,
        Uri uri,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient);
#pragma warning restore CA2000

        var loggerFactory = executionParameters?.LoggerFactory;
        var logger = loggerFactory?.CreateLogger(typeof(OpenApiKernelExtensions)) ?? NullLogger.Instance;

        var openApiSpec = await DocumentLoader.LoadDocumentFromUriAsync(
            uri,
            logger,
            httpClient,
            executionParameters?.AuthCallback,
            executionParameters?.UserAgent,
            cancellationToken).ConfigureAwait(false);

        return await CreateOpenApiPluginAsync(
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            uri,
            loggerFactory,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification.
    /// </summary>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="stream">A stream representing the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static async Task<KernelPlugin> CreateFromOpenApiAsync(
        string pluginName,
        Stream stream,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient);
#pragma warning restore CA2000

        var openApiSpec = await DocumentLoader.LoadDocumentFromStreamAsync(stream, cancellationToken).ConfigureAwait(false);

        return await CreateOpenApiPluginAsync(
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            loggerFactory: executionParameters?.LoggerFactory,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification.
    /// </summary>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="specification">The specification model.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static KernelPlugin CreateFromOpenApi(
        string pluginName,
        RestApiSpecification specification,
        OpenApiFunctionExecutionParameters? executionParameters = null)
    {
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient);
#pragma warning restore CA2000

        return CreateOpenApiPlugin(
            pluginName: pluginName,
            executionParameters: executionParameters,
            httpClient: httpClient,
            specification: specification);
    }

    /// <summary>
    /// Creates a plugin from an OpenAPI specification.
    /// </summary>
    internal static async Task<KernelPlugin> CreateOpenApiPluginAsync(
        string pluginName,
        OpenApiFunctionExecutionParameters? executionParameters,
        HttpClient httpClient,
        string pluginJson,
        Uri? documentUri = null,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
    {
        using var documentStream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(pluginJson));

        loggerFactory ??= NullLoggerFactory.Instance;

        var parser = new OpenApiDocumentParser(loggerFactory);

        var restApi = await parser.ParseAsync(
            stream: documentStream,
            options: new OpenApiDocumentParserOptions
            {
                IgnoreNonCompliantErrors = executionParameters?.IgnoreNonCompliantErrors ?? false,
                OperationSelectionPredicate = (context) => SelectOperations(context, executionParameters)
            },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return CreateOpenApiPlugin(
            pluginName: pluginName,
            executionParameters: executionParameters,
            httpClient: httpClient,
            specification: restApi,
            documentUri: documentUri,
            loggerFactory: loggerFactory);
    }

    /// <summary>
    /// Creates a plugin from an OpenAPI specification.
    /// </summary>
    internal static KernelPlugin CreateOpenApiPlugin(
        string pluginName,
        OpenApiFunctionExecutionParameters? executionParameters,
        HttpClient httpClient,
        RestApiSpecification specification,
        Uri? documentUri = null,
        ILoggerFactory? loggerFactory = null)
    {
        loggerFactory ??= NullLoggerFactory.Instance;

        var runner = new RestApiOperationRunner(
            httpClient,
            executionParameters?.AuthCallback,
            executionParameters?.UserAgent,
            executionParameters?.EnableDynamicPayload ?? true,
            executionParameters?.EnablePayloadNamespacing ?? false,
            executionParameters?.HttpResponseContentReader,
            executionParameters?.RestApiOperationResponseFactory);

        var functions = new List<KernelFunction>();
        ILogger logger = loggerFactory.CreateLogger(typeof(OpenApiKernelExtensions)) ?? NullLogger.Instance;
        foreach (var operation in specification.Operations)
        {
            try
            {
                logger.LogTrace("Registering Rest function {PluginName}.{OperationId}", pluginName, operation.Id);
                functions.Add(CreateRestApiFunction(pluginName, runner, specification.Info, specification.SecurityRequirements, operation, executionParameters, documentUri, loggerFactory));
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                // Logging the exception and keep registering other Rest functions
                logger.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {PluginName}.{OperationId}. Error: {Message}",
                    pluginName, operation.Id, ex.Message);
            }
        }

        specification.Freeze();

        return KernelPluginFactory.CreateFromFunctions(pluginName, specification.Info.Description, functions);
    }

    /// <summary>
    /// Registers <see cref="KernelFunctionFactory"/>> for a REST API operation.
    /// </summary>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="runner">The REST API operation runner.</param>
    /// <param name="info">The REST API info.</param>
    /// <param name="security">The REST API security requirements.</param>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="executionParameters">Function execution parameters.</param>
    /// <param name="documentUri">The URI of OpenAPI document.</param>
    /// <param name="loggerFactory">The logger factory.</param>
    /// <returns>An instance of <see cref="KernelFunctionFromPrompt"/> class.</returns>
    internal static KernelFunction CreateRestApiFunction(
        string pluginName,
        RestApiOperationRunner runner,
        RestApiInfo info,
        IList<RestApiSecurityRequirement>? security,
        RestApiOperation operation,
        OpenApiFunctionExecutionParameters? executionParameters,
        Uri? documentUri = null,
        ILoggerFactory? loggerFactory = null)
    {
        IReadOnlyList<RestApiParameter> restOperationParameters = operation.GetParameters(
            executionParameters?.EnableDynamicPayload ?? true,
            executionParameters?.EnablePayloadNamespacing ?? false,
            executionParameters?.ParameterFilter
        );

        var logger = loggerFactory?.CreateLogger(typeof(OpenApiKernelExtensions)) ?? NullLogger.Instance;

        async Task<RestApiOperationResponse> ExecuteAsync(Kernel kernel, KernelFunction function, KernelArguments variables, CancellationToken cancellationToken)
        {
            try
            {
                var options = new RestApiOperationRunOptions
                {
                    Kernel = kernel,
                    KernelFunction = function,
                    KernelArguments = variables,
                    ServerUrlOverride = executionParameters?.ServerUrlOverride,
                    ApiHostUrl = documentUri is not null ? new Uri(documentUri.GetLeftPart(UriPartial.Authority)) : null
                };

                return await runner.RunAsync(operation, variables, options, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                logger!.LogError(ex, "RestAPI function {Plugin}.{OperationId} execution failed with error {Error}", pluginName, operation.Id, ex.Message);
                throw;
            }
        }

        var parameters = restOperationParameters
            .Select(p => new KernelParameterMetadata(p.ArgumentName ?? p.Name)
            {
                Description = $"{p.Description ?? p.Name}",
                DefaultValue = p.DefaultValue ?? string.Empty,
                IsRequired = p.IsRequired,
                ParameterType = ConvertParameterDataType(p),
                Schema = p.Schema ?? (p.Type is null ? null : KernelJsonSchema.Parse($$"""{"type":"{{p.Type}}"}""")),
            })
            .ToList();

        var returnParameter = operation.GetDefaultReturnParameter();

        // Add unstructured metadata, specific to Open API, to the metadata property bag.
        var additionalMetadata = new Dictionary<string, object?>
        {
            { OpenApiKernelPluginFactory.OperationExtensionsMethodKey, operation.Method.ToString().ToUpperInvariant() },
            { OpenApiKernelPluginFactory.OperationExtensionsOperationKey, operation },
            { OpenApiKernelPluginFactory.OperationExtensionsInfoKey, info },
            { OpenApiKernelPluginFactory.OperationExtensionsSecurityKey, security },
            { OpenApiKernelPluginFactory.OperationExtensionsServerUrlsKey, operation.Servers is { Count: > 0 } servers && !string.IsNullOrEmpty(servers[0].Url) ? [servers[0].Url! ] : Array.Empty<string>() }
        };

        if (operation.Extensions is { Count: > 0 })
        {
            additionalMetadata.Add(OpenApiKernelPluginFactory.OperationExtensionsMetadataKey, operation.Extensions);
        }

        return KernelFunctionFactory.CreateFromMethod(
            method: ExecuteAsync,
            new KernelFunctionFromMethodOptions
            {
                FunctionName = ConvertOperationToValidFunctionName(operation, logger),
                Description = operation.Description,
                Parameters = parameters,
                ReturnParameter = returnParameter,
                LoggerFactory = loggerFactory,
                AdditionalMetadata = new ReadOnlyDictionary<string, object?>(additionalMetadata),
            });
    }

    #region private

    /// <summary>The metadata property bag key to use when storing the method of an operation.</summary>
    private const string OperationExtensionsMethodKey = "method";

    /// <summary>The metadata property bag key to use when storing the operation.</summary>
    private const string OperationExtensionsOperationKey = "operation";

    /// <summary>The metadata property bag key to use when storing the API information.</summary>
    private const string OperationExtensionsInfoKey = "info";

    /// <summary>The metadata property bag key to use when storing the security requirements.</summary>
    private const string OperationExtensionsSecurityKey = "security";

    /// <summary>The metadata property bag key to use when storing the server of an operation.</summary>
    private const string OperationExtensionsServerUrlsKey = "server-urls";

    /// <summary>The metadata property bag key to use for the list of extension values provided in the swagger file at the operation level.</summary>
    private const string OperationExtensionsMetadataKey = "operation-extensions";

    /// <summary>
    /// Converts operation id to valid <see cref="KernelFunction"/> name.
    /// A function name can contain only ASCII letters, digits, and underscores.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="logger">The logger.</param>
    /// <returns>Valid <see cref="KernelFunction"/>> name.</returns>
    private static string ConvertOperationToValidFunctionName(RestApiOperation operation, ILogger logger)
    {
        if (!string.IsNullOrWhiteSpace(operation.Id))
        {
            return ConvertOperationIdToValidFunctionName(operationId: operation.Id!, logger: logger);
        }

        // Tokenize operation path on forward and back slashes
        string[] tokens = operation.Path.Split('/', '\\');
        StringBuilder result = new();
        result.Append(CultureInfo.CurrentCulture.TextInfo.ToTitleCase(operation.Method.ToString()));

        foreach (string token in tokens)
        {
            // Removes all characters that are not ASCII letters, digits, and underscores.
            string formattedToken = RemoveInvalidCharsRegex().Replace(token, "");
            result.Append(CultureInfo.CurrentCulture.TextInfo.ToTitleCase(formattedToken.ToLower(CultureInfo.CurrentCulture)));
        }

        logger.LogInformation("""Operation method "{Method}" with path "{Path}" converted to "{Result}" to comply with SK Function name requirements. Use "{Result}" when invoking function.""", operation.Method, operation.Path, result, result);

        return result.ToString();
    }

    /// <summary>
    /// Converts operation id to valid <see cref="KernelFunction"/> name.
    /// A function name can contain only ASCII letters, digits, and underscores.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="logger">The logger.</param>
    /// <returns>Valid <see cref="KernelFunction"/> name.</returns>
    private static string ConvertOperationIdToValidFunctionName(string operationId, ILogger logger)
    {
        try
        {
            Verify.ValidFunctionName(operationId);
            return operationId;
        }
        catch (ArgumentException)
        {
            // The exception indicates that the operationId is not a valid function name.
            // To comply with the KernelFunction name requirements, it needs to be converted or sanitized.
            // Therefore, it should not be re-thrown, but rather swallowed to allow the conversion below.
        }

        // Tokenize operation id on forward and back slashes
        string[] tokens = operationId.Split('/', '\\');
        string result = string.Empty;

        foreach (string token in tokens)
        {
            // Removes all characters that are not ASCII letters, digits, and underscores.
            string formattedToken = RemoveInvalidCharsRegex().Replace(token, "");
            result += CultureInfo.CurrentCulture.TextInfo.ToTitleCase(formattedToken.ToLower(CultureInfo.CurrentCulture));
        }

        logger.LogInformation("""Operation name "{OperationId}" converted to "{Result}" to comply with SK Function name requirements. Use "{Result}" when invoking function.""", operationId, result, result);

        return result;
    }

    /// <summary>
    /// Selects operations to parse and import.
    /// </summary>
    /// <param name="context">Operation selection context.</param>
    /// <param name="executionParameters">Execution parameters.</param>
    /// <returns>True if the operation should be selected; otherwise, false.</returns>
    private static bool SelectOperations(OperationSelectionPredicateContext context, OpenApiFunctionExecutionParameters? executionParameters)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        if (executionParameters?.OperationSelectionPredicate is not null && executionParameters?.OperationsToExclude is { Count: > 0 })
        {
            throw new ArgumentException($"{nameof(executionParameters.OperationSelectionPredicate)} and {nameof(executionParameters.OperationsToExclude)} cannot be used together.");
        }

        if (executionParameters?.OperationSelectionPredicate is { } predicate)
        {
            return predicate(context);
        }

        return !executionParameters?.OperationsToExclude.Contains(context.Id ?? string.Empty) ?? true;
#pragma warning restore CS0618 // Type or member is obsolete
    }

    /// <summary>
    /// Converts the parameter type to a C# <see cref="Type"/> object.
    /// </summary>
    /// <param name="parameter">The REST API parameter.</param>
    private static Type? ConvertParameterDataType(RestApiParameter parameter)
    {
        return parameter.Type switch
        {
            "string" => typeof(string),
            "boolean" => typeof(bool),
            "number" => parameter.Format switch
            {
                "float" => typeof(float),
                "double" => typeof(double),
                _ => typeof(double)
            },
            "integer" => parameter.Format switch
            {
                "int32" => typeof(int),
                "int64" => typeof(long),
                _ => typeof(long)
            },
            "object" => typeof(object),
            _ => null
        };
    }

    /// <summary>
    /// Used to convert operationId to SK function names.
    /// </summary>
#if NET
    [GeneratedRegex("[^0-9A-Za-z_]")]
    private static partial Regex RemoveInvalidCharsRegex();
#else
    private static Regex RemoveInvalidCharsRegex() => s_removeInvalidCharsRegex;
    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z_./-/{/}]", RegexOptions.Compiled);
#endif

    #endregion
}
