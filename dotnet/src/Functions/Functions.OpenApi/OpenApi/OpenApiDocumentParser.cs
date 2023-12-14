// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.OpenApi.Any;
using Microsoft.OpenApi.Models;
using Microsoft.OpenApi.Readers;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Parser for OpenAPI documents.
/// </summary>
internal sealed class OpenApiDocumentParser : IOpenApiDocumentParser
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenApiDocumentParser"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenApiDocumentParser(ILoggerFactory? loggerFactory = null)
    {
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(OpenApiDocumentParser)) : NullLogger.Instance;
    }

    /// <inheritdoc/>
    public async Task<IList<RestApiOperation>> ParseAsync(
        Stream stream,
        bool ignoreNonCompliantErrors = false,
        IList<string>? operationsToExclude = null,
        CancellationToken cancellationToken = default)
    {
        var jsonObject = await this.DowngradeDocumentVersionToSupportedOneAsync(stream, cancellationToken).ConfigureAwait(false);

        using var memoryStream = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(jsonObject, JsonOptionsCache.WriteIndented));

        var result = await this._openApiReader.ReadAsync(memoryStream, cancellationToken).ConfigureAwait(false);

        this.AssertReadingSuccessful(result, ignoreNonCompliantErrors);

        return ExtractRestApiOperations(result.OpenApiDocument, operationsToExclude);
    }

    #region private

    /// <summary>
    /// Max depth to traverse down OpenAPI schema to discover payload properties.
    /// </summary>
    private const int PayloadPropertiesHierarchyMaxDepth = 10;

    /// <summary>
    /// Name of property that contains OpenAPI document version.
    /// </summary>
    private const string OpenApiVersionPropertyName = "openapi";

    /// <summary>
    /// Latest supported version of OpenAPI document.
    /// </summary>
    private static readonly Version s_latestSupportedVersion = new(3, 0, 1);

    /// <summary>
    /// List of supported Media Types.
    /// </summary>
    private static readonly List<string> s_supportedMediaTypes = new()
    {
        "application/json",
        "text/plain"
    };

    private readonly OpenApiStreamReader _openApiReader = new();
    private readonly ILogger _logger;

    /// <summary>
    /// Downgrades the version of an OpenAPI document to the latest supported one - 3.0.1.
    /// This class relies on Microsoft.OpenAPI.NET library to work with OpenAPI documents.
    /// The library, at the moment, does not support 3.1 spec, and the latest supported version is 3.0.1.
    /// There's an open issue tracking the support progress - https://github.com/microsoft/OpenAPI.NET/issues/795
    /// This method should be removed/revised as soon the support is added.
    /// </summary>
    /// <param name="stream">The original OpenAPI document stream.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>OpenAPI document with downgraded document version.</returns>
    private async Task<JsonObject> DowngradeDocumentVersionToSupportedOneAsync(Stream stream, CancellationToken cancellationToken)
    {
        var jsonObject = await ConvertContentToJsonAsync(stream, cancellationToken).ConfigureAwait(false) ?? throw new KernelException("Parsing of OpenAPI document failed.");
        if (!jsonObject.TryGetPropertyValue(OpenApiVersionPropertyName, out var propertyNode))
        {
            // The document is either malformed or has 2.x version that specifies document version in the 'swagger' property rather than in the 'openapi' one.
            return jsonObject;
        }

        if (propertyNode is not JsonValue value)
        {
            // The 'openapi' property has unexpected type.
            return jsonObject;
        }

        if (!Version.TryParse(value.ToString(), out var version))
        {
            // The 'openapi' property is malformed.
            return jsonObject;
        }

        if (version > s_latestSupportedVersion)
        {
            jsonObject[OpenApiVersionPropertyName] = s_latestSupportedVersion.ToString();
        }

        return jsonObject;
    }

    /// <summary>
    /// Converts YAML content to JSON content.
    /// The method uses SharpYaml library that comes as a not-direct dependency of Microsoft.OpenAPI.NET library.
    /// Should be replaced later when there's more convenient way to convert YAML content to JSON one.
    /// </summary>
    /// <param name="stream">The YAML/JSON content stream.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>JSON content stream.</returns>
    private static async Task<JsonObject?> ConvertContentToJsonAsync(Stream stream, CancellationToken cancellationToken = default)
    {
        var serializer = new SharpYaml.Serialization.Serializer();

        var obj = serializer.Deserialize(stream);

        using var memoryStream = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(obj)));

        return await JsonSerializer.DeserializeAsync<JsonObject>(memoryStream, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Parses an OpenAPI document and extracts REST API operations.
    /// </summary>
    /// <param name="document">The OpenAPI document.</param>
    /// <param name="operationsToExclude">Optional list of operations not to import, e.g. in case they are not supported</param>
    /// <returns>List of Rest operations.</returns>
    private static List<RestApiOperation> ExtractRestApiOperations(OpenApiDocument document, IList<string>? operationsToExclude = null)
    {
        var result = new List<RestApiOperation>();

        var serverUrl = document.Servers.FirstOrDefault()?.Url;

        foreach (var pathPair in document.Paths)
        {
            var operations = CreateRestApiOperations(serverUrl, pathPair.Key, pathPair.Value, operationsToExclude);

            result.AddRange(operations);
        }

        return result;
    }

    /// <summary>
    /// Creates REST API operation.
    /// </summary>
    /// <param name="serverUrl">The server url.</param>
    /// <param name="path">Rest resource path.</param>
    /// <param name="pathItem">Rest resource metadata.</param>
    /// <param name="operationsToExclude">Optional list of operations not to import, e.g. in case they are not supported</param>
    /// <returns>Rest operation.</returns>
    private static List<RestApiOperation> CreateRestApiOperations(string? serverUrl, string path, OpenApiPathItem pathItem, IList<string>? operationsToExclude = null)
    {
        var operations = new List<RestApiOperation>();

        foreach (var operationPair in pathItem.Operations)
        {
            var method = operationPair.Key.ToString();

            var operationItem = operationPair.Value;

            if (operationsToExclude != null && operationsToExclude.Contains(operationItem.OperationId, StringComparer.OrdinalIgnoreCase))
            {
                continue;
            }

            var operation = new RestApiOperation(
                operationItem.OperationId,
                string.IsNullOrEmpty(serverUrl) ? null : new Uri(serverUrl),
                path,
                new HttpMethod(method),
                string.IsNullOrEmpty(operationItem.Description) ? operationItem.Summary : operationItem.Description,
                CreateRestApiOperationParameters(operationItem.OperationId, operationItem.Parameters),
                CreateRestApiOperationPayload(operationItem.OperationId, operationItem.RequestBody),
                CreateRestApiOperationExpectedResponses(operationItem.Responses).ToDictionary(item => item.Item1, item => item.Item2)
            );

            operations.Add(operation);
        }

        return operations;
    }

    /// <summary>
    /// Creates REST API operation parameters.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="parameters">The OpenAPI parameters.</param>
    /// <returns>The parameters.</returns>
    private static List<RestApiOperationParameter> CreateRestApiOperationParameters(string operationId, IList<OpenApiParameter> parameters)
    {
        var result = new List<RestApiOperationParameter>();

        foreach (var parameter in parameters)
        {
            if (parameter.In == null)
            {
                throw new KernelException($"Parameter location of {parameter.Name} parameter of {operationId} operation is undefined.");
            }

            if (parameter.Style == null)
            {
                throw new KernelException($"Parameter style of {parameter.Name} parameter of {operationId} operation is undefined.");
            }

            var restParameter = new RestApiOperationParameter(
                parameter.Name,
                parameter.Schema.Type,
                parameter.Required,
                parameter.Explode,
                (RestApiOperationParameterLocation)Enum.Parse(typeof(RestApiOperationParameterLocation), parameter.In.ToString()!),
                (RestApiOperationParameterStyle)Enum.Parse(typeof(RestApiOperationParameterStyle), parameter.Style.ToString()!),
                parameter.Schema.Items?.Type,
                GetParameterValue(parameter.Schema.Default),
                parameter.Description,
                parameter.Schema.ToJsonSchema()
            );

            result.Add(restParameter);
        }

        return result;
    }

    /// <summary>
    /// Creates REST API operation payload.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="requestBody">The OpenAPI request body.</param>
    /// <returns>The REST API operation payload.</returns>
    private static RestApiOperationPayload? CreateRestApiOperationPayload(string operationId, OpenApiRequestBody requestBody)
    {
        if (requestBody?.Content == null)
        {
            return null;
        }

        var mediaType = s_supportedMediaTypes.FirstOrDefault(smt => requestBody.Content.ContainsKey(smt)) ?? throw new KernelException($"Neither of the media types of {operationId} is supported.");
        var mediaTypeMetadata = requestBody.Content[mediaType];

        var payloadProperties = GetPayloadProperties(operationId, mediaTypeMetadata.Schema, mediaTypeMetadata.Schema?.Required ?? new HashSet<string>());

        return new RestApiOperationPayload(mediaType, payloadProperties, requestBody.Description, mediaTypeMetadata?.Schema?.ToJsonSchema());
    }

    private static IEnumerable<(string, RestApiOperationExpectedResponse)> CreateRestApiOperationExpectedResponses(OpenApiResponses responses)
    {
        foreach (var response in responses)
        {
            var mediaType = s_supportedMediaTypes.FirstOrDefault(smt => response.Value.Content.ContainsKey(smt));
            if (mediaType is not null)
            {
                var matchingSchema = response.Value.Content[mediaType].Schema;
                var description = response.Value.Description ?? matchingSchema?.Description ?? string.Empty;

                yield return (response.Key, new RestApiOperationExpectedResponse(description, mediaType, matchingSchema?.ToJsonSchema()));
            }
        }
    }

    /// <summary>
    /// Returns REST API operation payload properties.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="schema">An OpenAPI document schema representing request body properties.</param>
    /// <param name="requiredProperties">List of required properties.</param>
    /// <param name="level">Current level in OpenAPI schema.</param>
    /// <returns>The REST API operation payload properties.</returns>
    private static List<RestApiOperationPayloadProperty> GetPayloadProperties(string operationId, OpenApiSchema? schema, ISet<string> requiredProperties,
        int level = 0)
    {
        if (schema == null)
        {
            return new List<RestApiOperationPayloadProperty>();
        }

        if (level > PayloadPropertiesHierarchyMaxDepth)
        {
            throw new KernelException($"Max level {PayloadPropertiesHierarchyMaxDepth} of traversing payload properties of {operationId} operation is exceeded.");
        }

        var result = new List<RestApiOperationPayloadProperty>();

        foreach (var propertyPair in schema.Properties)
        {
            var propertyName = propertyPair.Key;

            var propertySchema = propertyPair.Value;

            var property = new RestApiOperationPayloadProperty(
                propertyName,
                propertySchema.Type,
                requiredProperties.Contains(propertyName),
                GetPayloadProperties(operationId, propertySchema, requiredProperties, level + 1),
                propertySchema.Description,
                propertySchema.ToJsonSchema());

            result.Add(property);
        }

        return result;
    }

    /// <summary>
    /// Returns parameter value.
    /// </summary>
    /// <param name="valueMetadata">The value metadata.</param>
    /// <returns>The parameter value.</returns>
    private static string? GetParameterValue(IOpenApiAny valueMetadata)
    {
        if (valueMetadata is not IOpenApiPrimitive value)
        {
            return null;
        }

        return value.PrimitiveType switch
        {
            PrimitiveType.Integer => ((OpenApiInteger)value).Value.ToString(CultureInfo.InvariantCulture),
            PrimitiveType.Long => ((OpenApiLong)value).Value.ToString(CultureInfo.InvariantCulture),
            PrimitiveType.Float => ((OpenApiFloat)value).Value.ToString(CultureInfo.InvariantCulture),
            PrimitiveType.Double => ((OpenApiDouble)value).Value.ToString(CultureInfo.InvariantCulture),
            PrimitiveType.String => ((OpenApiString)value).Value.ToString(CultureInfo.InvariantCulture),
            PrimitiveType.Byte => Convert.ToBase64String(((OpenApiByte)value).Value),
            PrimitiveType.Binary => Encoding.UTF8.GetString(((OpenApiBinary)value).Value),
            PrimitiveType.Boolean => ((OpenApiBoolean)value).Value.ToString(CultureInfo.InvariantCulture),
            PrimitiveType.Date => ((OpenApiDate)value).Value.ToString("o").Substring(0, 10),
            PrimitiveType.DateTime => ((OpenApiDateTime)value).Value.ToString(CultureInfo.InvariantCulture),
            PrimitiveType.Password => ((OpenApiPassword)value).Value.ToString(CultureInfo.InvariantCulture),
            _ => throw new KernelException($"The value type - {value.PrimitiveType} is not supported."),
        };
    }

    /// <summary>
    /// Asserts the successful reading of OpenAPI document.
    /// </summary>
    /// <param name="readResult">The reading results to be checked.</param>
    /// <param name="ignoreNonCompliantErrors">Flag indicating whether to ignore non-compliant errors.
    /// If set to true, the parser will not throw exceptions for non-compliant documents.
    /// Please note that enabling this option may result in incomplete or inaccurate parsing results.
    /// </param>
    private void AssertReadingSuccessful(ReadResult readResult, bool ignoreNonCompliantErrors)
    {
        if (readResult.OpenApiDiagnostic.Errors.Any())
        {
            var message = $"Parsing of '{readResult.OpenApiDocument.Info?.Title}' OpenAPI document complete with the following errors: {string.Join(";", readResult.OpenApiDiagnostic.Errors)}";

            this._logger.LogWarning("{Message}", message);

            if (!ignoreNonCompliantErrors)
            {
                throw new KernelException(message);
            }
        }
    }

    #endregion
}
