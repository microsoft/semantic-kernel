// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Conventions;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Naming convention for storage properties based on provided name mapping.
/// </summary>
internal sealed class AzureCosmosDBMongoDBNamingConvention(IReadOnlyDictionary<string, string> nameMapping) : IMemberMapConvention
{
    private readonly IReadOnlyDictionary<string, string> _nameMapping = nameMapping;

    public string Name => nameof(AzureCosmosDBMongoDBNamingConvention);

    public void Apply(BsonMemberMap memberMap)
    {
        var memberName = memberMap.MemberName;
        var name = this._nameMapping.TryGetValue(memberName, out var customName) ? customName : memberName;

        memberMap.SetElementName(name);
    }
}
