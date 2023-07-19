// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Schema;

using System;
using System.Collections.Generic;

public sealed class SchemaDefinition
{
    public SchemaDefinition(
        string name,
        string? description,
        IEnumerable<SchemaTable> tables)
    {
        this.Name = name;
        this.Description = description;
        this.Tables = tables ?? Array.Empty<SchemaTable>();
    }

    public string Name { get; }

    public string? Description { get; }

    public IEnumerable<SchemaTable> Tables { get; }
}
