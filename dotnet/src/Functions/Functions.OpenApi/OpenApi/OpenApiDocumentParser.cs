// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics.CodeAnalysis;
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
using Microsoft.OpenApi.Interfaces;
using Microsoft.OpenApi.Models;
using Microsoft.OpenApi.Readers;
using Microsoft.OpenApi.Writers;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Parser for OpenAPI documents.
/// </summary>
public sealed class OpenApiDocumentParser(ILoggerFactory? loggerFactory = null)
{
    /// <summary>
    /// Parses OpenAPI document.
    /// </summary>
    /// <param name="stream">Stream containing OpenAPI document to parse.</param>
    /// <param name="options">Options for parsing OpenAPI document.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>Specification of the REST API.</returns>
    public async Task<RestApiSpecification> ParseAsync(Stream stream, OpenApiDocumentParserOptions? options = null, CancellationToken cancellationToken = default)
    {
        var jsonObject = await this.DowngradeDocumentVersionToSupportedOneAsync(stream, cancellationToken).ConfigureAwait(false);

        using var memoryStream = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(jsonObject, JsonOptionsCache.WriteIndented));

        var result = await this._openApiReader.ReadAsync(memoryStream, cancellationToken).ConfigureAwait(false);

        this.AssertReadingSuccessful(result, options?.IgnoreNonCompliantErrors ?? false);

        return new(
            ExtractRestApiInfo(result.OpenApiDocument),
            CreateRestApiOperationSecurityRequirements(result.OpenApiDocument.SecurityRequirements),
            ExtractRestApiOperations(result.OpenApiDocument, options, this._logger));
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
    private static readonly List<string> s_supportedMediaTypes =
    [
        "application/json",
        "text/plain"
    ];

    private readonly OpenApiStreamReader _openApiReader = new();
    private readonly ILogger _logger = loggerFactory?.CreateLogger(typeof(OpenApiDocumentParser)) ?? NullLogger.Instance;

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
    /// Parses an OpenAPI document and extracts REST API information.
    /// </summary>
    /// <param name="document">The OpenAPI document.</param>
    /// <returns>Rest API information.</returns>
    internal static RestApiInfo ExtractRestApiInfo(OpenApiDocument document)
    {
        return new()
        {
            Title = document.Info.Title,
            Description = document.Info.Description,
            Version = document.Info.Version,
        };
    }

    /// <summary>
    /// Parses an OpenAPI document and extracts REST API operations.
    /// </summary>
    /// <param name="document">The OpenAPI document.</param>
    /// <param name="options">Options for parsing OpenAPI document.</param>
    /// <param name="logger">Used to perform logging.</param>
    /// <returns>List of Rest operations.</returns>
    private static List<RestApiOperation> ExtractRestApiOperations(OpenApiDocument document, OpenApiDocumentParserOptions? options, ILogger logger)
    {
        var result = new List<RestApiOperation>();

        foreach (var pathPair in document.Paths)
        {
            var operations = CreateRestApiOperations(document, pathPair.Key, pathPair.Value, options, logger);
            result.AddRange(operations);
        }

        return result;
    }

    /// <summary>
    /// Creates REST API operation.
    /// </summary>
    /// <param name="document">The OpenAPI document.</param>
    /// <param name="path">Rest resource path.</param>
    /// <param name="pathItem">Rest resource metadata.</param>
    /// <param name="options">Options for parsing OpenAPI document.</param>
    /// <param name="logger">Used to perform logging.</param>
    /// <returns>Rest operation.</returns>
    internal static List<RestApiOperation> CreateRestApiOperations(OpenApiDocument document, string path, OpenApiPathItem pathItem, OpenApiDocumentParserOptions? options, ILogger logger)
    {
        try
        {
            var operations = new List<RestApiOperation>();
            var globalServers = CreateRestApiOperationServers(document.Servers);
            var pathServers = CreateRestApiOperationServers(pathItem.Servers);

            foreach (var operationPair in pathItem.Operations)
            {
                var method = operationPair.Key.ToString();
                var operationItem = operationPair.Value;
                var operationServers = CreateRestApiOperationServers(operationItem.Servers);

                // Skip the operation parsing and don't add it to the result operations list if it's explicitly excluded by the predicate.
                if (!options?.OperationSelectionPredicate?.Invoke(new OperationSelectionPredicateContext(operationItem.OperationId, path, method, operationItem.Description)) ?? false)
                {
                    continue;
                }

                try
                {
                    var operation = new RestApiOperation(
                        id: operationItem.OperationId,
                        servers: globalServers,
                        pathServers: pathServers,
                        operationServers: operationServers,
                        path: path,
                        method: new HttpMethod(method),
                        description: string.IsNullOrEmpty(operationItem.Description) ? operationItem.Summary : operationItem.Description,
                        parameters: CreateRestApiOperationParameters(operationItem.OperationId, operationItem.Parameters.Union(pathItem.Parameters, s_parameterNameAndLocationComparer)),
                        payload: CreateRestApiOperationPayload(operationItem.OperationId, operationItem.RequestBody),
                        responses: CreateRestApiOperationExpectedResponses(operationItem.Responses).ToDictionary(static item => item.Item1, static item => item.Item2),
                        securityRequirements: CreateRestApiOperationSecurityRequirements(operationItem.Security)
                    )
                    {
                        Extensions = CreateRestApiOperationExtensions(operationItem.Extensions, logger)
                    };

                    operations.Add(operation);
                }
                catch (KernelException ke)
                {
                    logger.LogWarning(ke, "Error occurred creating REST API operation for {OperationId}. Operation will be ignored.", operationItem.OperationId);
                }
            }

            return operations;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Fatal error occurred during REST API operation creation.");
            throw;
        }
    }

    private static readonly ParameterNameAndLocationComparer s_parameterNameAndLocationComparer = new();

    /// <summary>
    /// Compares two <see cref="OpenApiParameter"/> objects by their name and location.
    /// </summary>
    private sealed class ParameterNameAndLocationComparer : IEqualityComparer<OpenApiParameter>
    {
        public bool Equals(OpenApiParameter? x, OpenApiParameter? y)
        {
            if (x is null || y is null)
            {
                return x == y;
            }
            return this.GetHashCode(x) == this.GetHashCode(y);
        }
        public int GetHashCode([DisallowNull] OpenApiParameter obj)
        {
            return HashCode.Combine(obj.Name, obj.In);
        }
    }

    /// <summary>
    /// Build a list of <see cref="RestApiServer"/> objects from the given list of <see cref="OpenApiServer"/> objects.
    /// </summary>
    /// <param name="servers">Represents servers which hosts the REST API.</param>
    private static List<RestApiServer> CreateRestApiOperationServers(IList<OpenApiServer> servers)
    {
        if (servers == null || servers.Count == 0)
        {
            return new List<RestApiServer>();
        }

        var result = new List<RestApiServer>(servers.Count);
        foreach (var server in servers)
        {
            var variables = server.Variables.ToDictionary(item => item.Key, item => new RestApiServerVariable(item.Value.Default, item.Value.Description, item.Value.Enum));
            result.Add(new RestApiServer(server.Url, variables, server.Description));
        }

        return result;
    }

    /// <summary>
    /// Build a <see cref="RestApiSecurityScheme"/> objects from the given <see cref="OpenApiSecurityScheme"/> object.
    /// </summary>
    /// <param name="securityScheme">The REST API security scheme.</param>
    private static RestApiSecurityScheme CreateRestApiSecurityScheme(OpenApiSecurityScheme securityScheme)
    {
        return new RestApiSecurityScheme()
        {
            SecuritySchemeType = securityScheme.Type.ToString(),
            Description = securityScheme.Description,
            Name = securityScheme.Name,
            In = (RestApiParameterLocation)Enum.Parse(typeof(RestApiParameterLocation), securityScheme.In.ToString()!),
            Scheme = securityScheme.Scheme,
            BearerFormat = securityScheme.BearerFormat,
            Flows = CreateRestApiOAuthFlows(securityScheme.Flows),
            OpenIdConnectUrl = securityScheme.OpenIdConnectUrl
        };
    }

    /// <summary>
    /// Build a <see cref="RestApiOAuthFlows"/> object from the given <see cref="OpenApiOAuthFlows"/> object.
    /// </summary>
    /// <param name="flows">The REST API OAuth flows.</param>
    private static RestApiOAuthFlows? CreateRestApiOAuthFlows(OpenApiOAuthFlows? flows)
    {
        return flows is not null ? new RestApiOAuthFlows()
        {
            Implicit = CreateRestApiOAuthFlow(flows.Implicit),
            Password = CreateRestApiOAuthFlow(flows.Password),
            ClientCredentials = CreateRestApiOAuthFlow(flows.ClientCredentials),
            AuthorizationCode = CreateRestApiOAuthFlow(flows.AuthorizationCode),
        } : null;
    }

    /// <summary>
    /// Build a <see cref="RestApiOAuthFlow"/> object from the given <see cref="OpenApiOAuthFlow"/> object.
    /// </summary>
    /// <param name="flow">The REST API OAuth flow.</param>
    private static RestApiOAuthFlow? CreateRestApiOAuthFlow(OpenApiOAuthFlow? flow)
    {
        return flow is not null ? new RestApiOAuthFlow()
        {
            AuthorizationUrl = flow.AuthorizationUrl,
            TokenUrl = flow.TokenUrl,
            RefreshUrl = flow.RefreshUrl,
            Scopes = new ReadOnlyDictionary<string, string>(flow.Scopes ?? new Dictionary<string, string>())
        } : null;
    }

    /// <summary>
    /// Build a list of <see cref="RestApiSecurityRequirement"/> objects from the given <see cref="OpenApiSecurityRequirement"/> objects.
    /// </summary>
    /// <param name="security">The REST API security.</param>
    internal static List<RestApiSecurityRequirement> CreateRestApiOperationSecurityRequirements(IList<OpenApiSecurityRequirement>? security)
    {
        var operationRequirements = new List<RestApiSecurityRequirement>();

        if (security is not null)
        {
            foreach (var item in security)
            {
                foreach (var keyValuePair in item)
                {
                    if (keyValuePair.Key is not OpenApiSecurityScheme openApiSecurityScheme)
                    {
                        throw new KernelException("The security scheme is not supported.");
                    }

                    operationRequirements.Add(new RestApiSecurityRequirement(new Dictionary<RestApiSecurityScheme, IList<string>> { { CreateRestApiSecurityScheme(openApiSecurityScheme), keyValuePair.Value } }));
                }
            }
        }

        return operationRequirements;
    }

    /// <summary>
    /// Build a dictionary of extension key value pairs from the given open api extension model, where the key is the extension name
    /// and the value is either the actual value in the case of primitive types like string, int, date, etc, or a json string in the
    /// case of complex types.
    /// </summary>
    /// <param name="extensions">The dictionary of extension properties in the open api model.</param>
    /// <param name="logger">Used to perform logging.</param>
    /// <returns>The dictionary of extension properties using a simplified model that doesn't use any open api models.</returns>
    /// <exception cref="KernelException">Thrown when any extension data types are encountered that are not supported.</exception>
    private static Dictionary<string, object?> CreateRestApiOperationExtensions(IDictionary<string, IOpenApiExtension> extensions, ILogger logger)
    {
        var result = new Dictionary<string, object?>();

        // Map each extension property.
        foreach (var extension in extensions)
        {
            if (extension.Value is IOpenApiPrimitive primitive)
            {
                // Set primitive values directly into the dictionary.
                object? extensionValueObj = GetParameterValue(primitive, "extension property", extension.Key);
                result.Add(extension.Key, extensionValueObj);
            }
            else if (extension.Value is IOpenApiAny any)
            {
                // Serialize complex objects and set as json strings.
                // The only remaining type not referenced here is null, but the default value of extensionValueObj
                // is null, so if we just continue that will handle the null case.
                if (any.AnyType is AnyType.Array or AnyType.Object)
                {
                    var schemaBuilder = new StringBuilder();
                    var jsonWriter = new OpenApiJsonWriter(new StringWriter(schemaBuilder, CultureInfo.InvariantCulture), new OpenApiJsonWriterSettings() { Terse = true });
                    extension.Value.Write(jsonWriter, Microsoft.OpenApi.OpenApiSpecVersion.OpenApi3_0);
                    object? extensionValueObj = schemaBuilder.ToString();
                    result.Add(extension.Key, extensionValueObj);
                }
            }
            else
            {
                logger.LogWarning("The type of extension property '{ExtensionPropertyName}' is not supported while trying to consume the OpenApi schema.", extension.Key);
            }
        }

        return result;
    }

    /// <summary>
    /// Creates REST API parameters.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="parameters">The OpenAPI parameters.</param>
    /// <returns>The parameters.</returns>
    private static List<RestApiParameter> CreateRestApiOperationParameters(string operationId, IEnumerable<OpenApiParameter> parameters)
    {
        var result = new List<RestApiParameter>();

        foreach (var parameter in parameters)
        {
            if (parameter.In is null)
            {
                throw new KernelException($"Parameter location of {parameter.Name} parameter of {operationId} operation is undefined.");
            }

            if (parameter.Style is null)
            {
                throw new KernelException($"Parameter style of {parameter.Name} parameter of {operationId} operation is undefined.");
            }

            var restParameter = new RestApiParameter(
                parameter.Name,
                parameter.Schema.Type,
                parameter.Required,
                parameter.Explode,
                (RestApiParameterLocation)Enum.Parse(typeof(RestApiParameterLocation), parameter.In.ToString()!),
                (RestApiParameterStyle)Enum.Parse(typeof(RestApiParameterStyle), parameter.Style.ToString()!),
                parameter.Schema.Items?.Type,
                GetParameterValue(parameter.Schema.Default, "parameter", parameter.Name),
                parameter.Description,
                parameter.Schema.Format,
                parameter.Schema.ToJsonSchema()
            );

            result.Add(restParameter);
        }

        return result;
    }

    /// <summary>
    /// Creates REST API payload.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="requestBody">The OpenAPI request body.</param>
    /// <returns>The REST API payload.</returns>
    private static RestApiPayload? CreateRestApiOperationPayload(string operationId, OpenApiRequestBody requestBody)
    {
        if (requestBody?.Content is null)
        {
            return null;
        }

        var mediaType = GetMediaType(requestBody.Content) ?? throw new KernelException($"Neither of the media types of {operationId} is supported.");
        var mediaTypeMetadata = requestBody.Content[mediaType];

        var payloadProperties = GetPayloadProperties(operationId, mediaTypeMetadata.Schema);

        return new RestApiPayload(mediaType, payloadProperties, requestBody.Description, mediaTypeMetadata?.Schema?.ToJsonSchema());
    }

    /// <summary>
    /// Returns the first supported media type. If none of the media types are supported, an exception is thrown.
    /// </summary>
    /// <remarks>
    /// Handles the case when the media type contains additional parameters e.g. application/json; x-api-version=2.0.
    /// </remarks>
    /// <param name="content">The OpenAPI request body content.</param>
    /// <returns>The first support ed media type.</returns>
    /// <exception cref="KernelException"></exception>
    private static string? GetMediaType(IDictionary<string, OpenApiMediaType> content)
    {
        foreach (var mediaType in s_supportedMediaTypes)
        {
            foreach (var key in content.Keys)
            {
                var keyParts = key.Split(';');
                if (keyParts[0].Equals(mediaType, StringComparison.OrdinalIgnoreCase))
                {
                    return key;
                }
            }
        }
        return null;
    }

    /// <summary>
    /// Create collection of expected responses for the REST API operation for the supported media types.
    /// </summary>
    /// <param name="responses">Responses from the OpenAPI endpoint.</param>
    private static IEnumerable<(string, RestApiExpectedResponse)> CreateRestApiOperationExpectedResponses(OpenApiResponses responses)
    {
        foreach (var response in responses)
        {
            var mediaType = GetMediaType(response.Value.Content);
            if (mediaType is not null)
            {
                var matchingSchema = response.Value.Content[mediaType].Schema;
                var description = response.Value.Description ?? matchingSchema?.Description ?? string.Empty;

                yield return (response.Key, new RestApiExpectedResponse(description, mediaType, matchingSchema?.ToJsonSchema()));
            }
        }
    }

    /// <summary>
    /// Returns REST API payload properties.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="schema">An OpenAPI document schema representing request body properties.</param>
    /// <param name="level">Current level in OpenAPI schema.</param>
    /// <returns>The REST API payload properties.</returns>
    private static List<RestApiPayloadProperty> GetPayloadProperties(string operationId, OpenApiSchema? schema, int level = 0)
    {
        if (schema is null)
        {
            return [];
        }

        if (level > PayloadPropertiesHierarchyMaxDepth)
        {
            throw new KernelException($"Max level {PayloadPropertiesHierarchyMaxDepth} of traversing payload properties of {operationId} operation is exceeded.");
        }

        var result = new List<RestApiPayloadProperty>();

        foreach (var propertyPair in schema.Properties)
        {
            var propertyName = propertyPair.Key;

            var propertySchema = propertyPair.Value;

            var property = new RestApiPayloadProperty(
                propertyName,
                propertySchema.Type,
                schema.Required.Contains(propertyName),
                GetPayloadProperties(operationId, propertySchema, level + 1),
                propertySchema.Description,
                propertySchema.Format,
                propertySchema.ToJsonSchema(),
                GetParameterValue(propertySchema.Default, "payload property", propertyName));

            result.Add(property);
        }

        return result;
    }

    /// <summary>
    /// Returns parameter value.
    /// </summary>
    /// <param name="valueMetadata">The value metadata.</param>
    /// <param name="entityDescription">A description of the type of entity we are trying to get a value for.</param>
    /// <param name="entityName">The name of the entity that we are trying to get the value for.</param>
    /// <returns>The parameter value.</returns>
    private static object? GetParameterValue(IOpenApiAny valueMetadata, string entityDescription, string entityName)
    {
        if (valueMetadata is not IOpenApiPrimitive value)
        {
            return null;
        }

        return value.PrimitiveType switch
        {
            PrimitiveType.Integer => ((OpenApiInteger)value).Value,
            PrimitiveType.Long => ((OpenApiLong)value).Value,
            PrimitiveType.Float => ((OpenApiFloat)value).Value,
            PrimitiveType.Double => ((OpenApiDouble)value).Value,
            PrimitiveType.String => ((OpenApiString)value).Value,
            PrimitiveType.Byte => ((OpenApiByte)value).Value,
            PrimitiveType.Binary => ((OpenApiBinary)value).Value,
            PrimitiveType.Boolean => ((OpenApiBoolean)value).Value,
            PrimitiveType.Date => ((OpenApiDate)value).Value,
            PrimitiveType.DateTime => ((OpenApiDateTime)value).Value,
            PrimitiveType.Password => ((OpenApiPassword)value).Value,
            _ => throw new KernelException($"The value type '{value.PrimitiveType}' of {entityDescription} '{entityName}' is not supported."),
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
            var title = readResult.OpenApiDocument.Info?.Title;
            var errors = string.Join(";", readResult.OpenApiDiagnostic.Errors);

            if (!ignoreNonCompliantErrors)
            {
                var exception = new KernelException($"Parsing of '{title}' OpenAPI document complete with the following errors: {errors}");
                this._logger.LogError(exception, "Parsing of '{Title}' OpenAPI document complete with the following errors: {Errors}", title, errors);
                throw exception;
            }

            this._logger.LogWarning("Parsing of '{Title}' OpenAPI document complete with the following errors: {Errors}", title, errors);
        }
    }

    #endregion
}
