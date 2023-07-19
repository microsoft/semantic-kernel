// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Schema;

using System.Text.Json.Serialization;

public sealed class SchemaColumn
{
    public SchemaColumn(
        string name,
        string? description,
        string type,
        bool isPrimary,
        string? referencedTable = null,
        string? referencedColumn = null)
    {
        this.Name = name;
        this.Description = description;
        this.Type = type;
        this.IsPrimary = isPrimary;
        this.ReferencedTable = referencedTable;
        this.ReferencedColumn = referencedColumn;
    }

    public string Name { get; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public string? Description { get; }

    public string Type { get; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool IsPrimary { get; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public string? ReferencedTable { get; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public string? ReferencedColumn { get; }
}
