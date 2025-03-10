// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

#pragma warning disable CA2007, VSTHRD111 // .ConfigureAwait(false)

namespace StructuredDataPlugin;

/// <summary>
/// Represents a product entity in the database.
/// </summary>
public sealed class Product
{
    /// <summary>
    /// The unique identifier for the product.
    /// </summary>
    [Description("The unique identifier for the product.")]
    [Key, DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public Guid? Id { get; set; }

    /// <summary>
    /// The description of the product.
    /// </summary>
    [Description("The description of the product.")]
    public string? Description { get; set; }

    /// <summary>
    /// The date the product was created.
    /// </summary>
    [Description("The date the product was created")]
    public DateTime? DateCreated { get; set; }
}
