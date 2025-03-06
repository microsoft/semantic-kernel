// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using Microsoft.Extensions.Configuration;

#pragma warning disable CA2007, VSTHRD111 // .ConfigureAwait(false)

namespace StructuredDataConnector;

internal sealed class MyDbContext : DbContext
{
    public MyDbContext(IConfiguration config) :
        base(config[$"ConnectionStrings:{nameof(MyDbContext)}"]!)
    {
    }

    public MyDbContext(string connectionString)
        : base(connectionString)
    {
    }

    protected override void OnModelCreating(DbModelBuilder modelBuilder)
    {
        Database.SetInitializer<MyDbContext>(null);
        modelBuilder.Entity<MyEntity>().ToTable("Test1");
        base.OnModelCreating(modelBuilder);
    }
}
