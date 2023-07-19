// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Schema;

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

public sealed class SchemaTable
{
    public SchemaTable(
        string name,
        string? description = null,
        bool isView = false,
        IEnumerable<SchemaColumn>? columns = null)
    {
        this.Name = name;
        this.Description = description;
        this.Columns = columns ?? Array.Empty<SchemaColumn>();
        this.IsView = isView;
    }

    public string Name { get; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public string? Description { get; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool IsView { get; }

    public IEnumerable<SchemaColumn> Columns { get; }
}
