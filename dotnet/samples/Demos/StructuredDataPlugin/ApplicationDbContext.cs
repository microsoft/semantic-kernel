// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using Microsoft.Extensions.Configuration;

namespace StructuredDataPlugin;

/// <summary>
/// Represents a database context for the structured data plugin demo.
/// Inherits from Entity Framework's DbContext to provide database access and management.
/// </summary>
internal sealed class ApplicationDbContext : DbContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ApplicationDbContext"/> class using configuration settings.
    /// </summary>
    /// <param name="config">The configuration object containing connection string information.</param>
    /// <remarks>
    /// The connection string is retrieved from the configuration using the pattern "ConnectionStrings:ApplicationDbContext".
    /// </remarks>
    public ApplicationDbContext(IConfiguration config) :
        base(config[$"ConnectionStrings:{nameof(ApplicationDbContext)}"]!)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ApplicationDbContext"/> class using a direct connection string.
    /// </summary>
    /// <param name="connectionString">The connection string to the database.</param>
    public ApplicationDbContext(string connectionString)
        : base(connectionString)
    {
    }

    /// <summary>
    /// Configures the database model and its relationships.
    /// </summary>
    /// <param name="modelBuilder">The builder being used to construct the model for this context.</param>
    /// <remarks>
    /// This method:
    /// - Disables database initialization
    /// - Maps the Product entity to the "Products" table
    /// - Calls the base configuration
    /// </remarks>
    protected override void OnModelCreating(DbModelBuilder modelBuilder)
    {
        Database.SetInitializer<ApplicationDbContext>(null);
        modelBuilder.Entity<Product>().ToTable("Products");
        base.OnModelCreating(modelBuilder);
    }
}
