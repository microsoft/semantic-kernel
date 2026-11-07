// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

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
    [Description("The name of the product.")]
    public string? Name { get; set; }

    /// <summary>
    /// The price of the product.
    /// </summary>
    [Description("The price of the product in USD.")]
    public decimal? Price { get; set; }

    /// <summary>
    /// The date the product was created.
    /// </summary>
    [Description("The date the product was created")]
    [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
    public DateTime? DateCreated { get; set; }
}

/// <summary>
/// Information the model may provide when creating a product.
/// </summary>
internal sealed class CreateProductRequest
{
    /// <summary>
    /// Gets or sets the product name.
    /// </summary>
    [Description("The name of the product.")]
    public string? Name { get; set; }

    /// <summary>
    /// Gets or sets the product price.
    /// </summary>
    [Description("The price of the product in USD.")]
    public decimal? Price { get; set; }
}

/// <summary>
/// Information the model may provide when updating a product.
/// </summary>
internal sealed class UpdateProductRequest
{
    /// <summary>
    /// Gets or sets the unique product identifier.
    /// </summary>
    [Description("The unique identifier of the product to update.")]
    public Guid Id { get; set; }

    /// <summary>
    /// Gets or sets the replacement price.
    /// </summary>
    [Description("The new price of the product in USD.")]
    public decimal? Price { get; set; }
}

/// <summary>
/// Information the model may provide when deleting a product.
/// </summary>
internal sealed class DeleteProductRequest
{
    /// <summary>
    /// Gets or sets the unique product identifier.
    /// </summary>
    [Description("The unique identifier of the product to delete.")]
    public Guid Id { get; set; }
}
