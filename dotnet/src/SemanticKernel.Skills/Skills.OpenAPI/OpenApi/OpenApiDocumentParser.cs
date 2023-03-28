// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using Microsoft.OpenApi.Any;
using Microsoft.OpenApi.Models;
using Microsoft.OpenApi.Readers;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;

/// <summary>
/// Parser for OpenAPI documents.
/// </summary>
internal class OpenApiDocumentParser : IOpenApiDocumentParser
{
    /// <inheritdoc/>
    public IList<RestApiOperation> Parse(Stream stream)
    {
        var openApiDocument = new OpenApiStreamReader().Read(stream, out var diagnostic);

        if (diagnostic.Errors.Any())
        {
            throw new OpenApiDocumentParsingException($"Parsing of '{openApiDocument.Info?.Title}' OpenAPI document failed. Details: {string.Join(';', diagnostic.Errors)}");
        }

        return ExtractRestOperations(openApiDocument);
    }

    #region private

    /// <summary>
    /// Parses an OpenApi document and extracts Rest operations.
    /// </summary>
    /// <param name="document">The OpenApi document.</param>
    /// <returns>List of Rest operations.</returns>
    private static IList<RestApiOperation> ExtractRestOperations(OpenApiDocument document)
    {
        var result = new List<RestApiOperation>();

        var serverUrl = document.Servers.First().Url;

        foreach (var pathPair in document.Paths)
        {
            var operations = CreateRestOperations(serverUrl, pathPair.Key, pathPair.Value);

            result.AddRange(operations);
        }

        return result;
    }

    /// <summary>
    /// Creates Rest operation.
    /// </summary>
    /// <param name="path">Rest resource path.</param>
    /// <param name="pathItem">Rest resource metadata.</param>
    /// <param name="serverUrl">The server url.</param>
    /// <returns>Rest operation.</returns>
    private static IList<RestApiOperation> CreateRestOperations(string serverUrl, string path, OpenApiPathItem pathItem)
    {
        var result = new List<RestApiOperation>();

        foreach (var operationPair in pathItem.Operations)
        {
            var method = operationPair.Key.ToString();

            var operationItem = operationPair.Value;

            var restOperation = new RestApiOperation(
                operationItem!.OperationId,
                operationItem!.Description,
                path,
                new HttpMethod(method),
                serverUrl
            );

            restOperation.AddParameters(ConvertParameters(operationItem!.Parameters));

            result.Add(restOperation);
        }

        return result;
    }

    private static IList<RestApiOperationParameter> ConvertParameters(IList<OpenApiParameter> parameters)
    {
        var restParameters = new List<RestApiOperationParameter>();

        foreach (var parameter in parameters)
        {
            if (parameter.In == null)
            {
                throw new OpenApiDocumentParsingException($"Parameter location of {parameter.Name} parameter is undefined.");
            }

            var restParameter = new RestApiOperationParameter(
                parameter.Name,
                parameter.Required,
                (RestApiOperationParameterType)parameter.In, //TODO: Do a proper enum mapping,
                (parameter.Schema.Default as OpenApiString)?.Value ?? string.Empty
            );

            restParameters.Add(restParameter);
        }

        return restParameters;
    }

    #endregion
}
