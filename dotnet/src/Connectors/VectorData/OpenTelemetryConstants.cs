// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// OpenTelemetry constants from Semantic Conventions for database calls and systems:
/// <see href="https://opentelemetry.io/docs/specs/semconv/database"/>.
/// <see href="https://opentelemetry.io/docs/specs/semconv/database/database-metrics"/>.
/// <see href="https://opentelemetry.io/docs/specs/semconv/database/database-spans"/>.
/// </summary>
internal static class OpenTelemetryConstants
{
    public const string DefaultSourceName = "Experimental.Microsoft.Extensions.VectorData";

    public const string DbSystemName = "db.system.name";
    public const string DbCollectionName = "db.collection.name";
    public const string DbNamespace = "db.namespace";
    public const string DbOperationName = "db.operation.name";

    public const string DbOperationDurationMetricName = "db.client.operation.duration";
    public const string DbOperationDurationMetricDescription = "Duration of database client operations.";

    public const string ErrorType = "error.type";

    public const string SecondsUnit = "s";

    public static string GetSourceNameOrDefault(string? sourceName) => !string.IsNullOrWhiteSpace(sourceName) ? sourceName! : DefaultSourceName;

    public static string GetActivityName(string operationName, string? collectionName, string? namespaceName)
    {
        if (!string.IsNullOrWhiteSpace(collectionName))
        {
            return $"{operationName} {collectionName}";
        }

        if (!string.IsNullOrWhiteSpace(namespaceName))
        {
            return $"{operationName} {namespaceName}";
        }

        return operationName;
    }
}
