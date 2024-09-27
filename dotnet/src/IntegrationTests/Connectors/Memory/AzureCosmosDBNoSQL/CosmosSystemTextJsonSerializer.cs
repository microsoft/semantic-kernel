// Copyright (c) Microsoft. All rights reserved.

// Taken from https://github.com/Azure/azure-cosmos-dotnet-v3/pull/4332
// TODO: Remove when https://github.com/Azure/azure-cosmos-dotnet-v3/pull/4589 will be released.

using System;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.Azure.Cosmos;

/// <summary>
/// This class provides a default implementation of System.Text.Json Cosmos Linq Serializer.
/// </summary>
internal sealed class CosmosSystemTextJsonSerializer : CosmosLinqSerializer
{
    /// <summary>
    /// A read-only instance of <see cref="JsonSerializerOptions"/>.
    /// </summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>
    /// Creates an instance of <see cref="CosmosSystemTextJsonSerializer"/>
    /// with the default values for the Cosmos SDK
    /// </summary>
    /// <param name="jsonSerializerOptions">An instance of <see cref="JsonSerializerOptions"/> containing the json serialization options.</param>
    public CosmosSystemTextJsonSerializer(
        JsonSerializerOptions jsonSerializerOptions)
    {
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    /// <inheritdoc/>
    [return: MaybeNull]
    public override T FromStream<T>(Stream stream)
    {
        if (stream == null)
        {
            throw new ArgumentNullException(nameof(stream));
        }

        if (stream.CanSeek && stream.Length == 0)
        {
            return default;
        }

        if (typeof(Stream).IsAssignableFrom(typeof(T)))
        {
            return (T)(object)stream;
        }

        using (stream)
        {
            return JsonSerializer.Deserialize<T>(stream, this._jsonSerializerOptions);
        }
    }

    /// <inheritdoc/>
    public override Stream ToStream<T>(T input)
    {
        MemoryStream streamPayload = new();
        JsonSerializer.Serialize(
            utf8Json: streamPayload,
            value: input,
            options: this._jsonSerializerOptions);

        streamPayload.Position = 0;
        return streamPayload;
    }

    /// <summary>
    /// Convert a MemberInfo to a string for use in LINQ query translation.
    /// </summary>
    /// <param name="memberInfo">Any MemberInfo used in the query.</param>
    /// <returns>A serialized representation of the member.</returns>
    /// <remarks>
    /// Note that this is just a default implementation which handles the basic scenarios. Any <see cref="JsonSerializerOptions"/> passed in
    /// here are not going to be reflected in SerializeMemberName(). For example, if customers passed in a JsonSerializerOption such as below
    /// <code language="c#">
    /// <![CDATA[
    /// JsonSerializerOptions options = new()
    /// {
    ///     PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    /// }
    /// ]]>
    /// </code>
    /// This would not be honored by SerializeMemberName() unless it included special handling for this, for example.
    /// <code language="c#">
    /// <![CDATA[
    /// public override string SerializeMemberName(MemberInfo memberInfo)
    /// {
    ///     JsonExtensionDataAttribute jsonExtensionDataAttribute =
    ///         memberInfo.GetCustomAttribute<JsonExtensionDataAttribute>(true);
    ///     if (jsonExtensionDataAttribute != null)
    ///     {
    ///         return null;
    ///     }
    ///     JsonPropertyNameAttribute jsonPropertyNameAttribute = memberInfo.GetCustomAttribute<JsonPropertyNameAttribute>(true);
    ///     if (!string.IsNullOrEmpty(jsonPropertyNameAttribute?.Name))
    ///     {
    ///         return jsonPropertyNameAttribute.Name;
    ///     }
    ///     return System.Text.Json.JsonNamingPolicy.CamelCase.ConvertName(memberInfo.Name);
    /// }
    /// ]]>
    /// </code>
    /// To handle such scenarios, please create a custom serializer which inherits from the <see cref="CosmosSystemTextJsonSerializer"/> and overrides the
    /// SerializeMemberName to add any special handling.
    /// </remarks>
    public override string? SerializeMemberName(MemberInfo memberInfo)
    {
        JsonExtensionDataAttribute? jsonExtensionDataAttribute =
             memberInfo.GetCustomAttribute<JsonExtensionDataAttribute>(true);

        if (jsonExtensionDataAttribute != null)
        {
            return null;
        }

        JsonPropertyNameAttribute? jsonPropertyNameAttribute = memberInfo.GetCustomAttribute<JsonPropertyNameAttribute>(true);
        if (jsonPropertyNameAttribute is { } && !string.IsNullOrEmpty(jsonPropertyNameAttribute.Name))
        {
            return jsonPropertyNameAttribute.Name;
        }

        return memberInfo.Name;
    }
}
