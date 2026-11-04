// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Data.Entity;
using System.Data.Entity.Infrastructure;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.StructuredData;

public class StructuredDataServiceTests
{
    [Fact]
    public void ConstructorWithConnectionStringCreatesContext()
    {
        // Act
        using var service = new StructuredDataService<TestDbContext>("TestConnection");

        // Assert
        Assert.NotNull(service.Context);
    }

    [Fact]
    public void ConstructorWithNullDbContextThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new StructuredDataService<TestDbContext>(dbContext: null!));
    }

    [Fact]
    public void CreateStructuredDataPluginWithoutOperationsIncludesOnlySelect()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act
        var plugin = StructuredDataPluginFactory.CreateStructuredDataPlugin<TestDbContext, TestEntity>(service);

        // Assert
        Assert.Equal(1, plugin.FunctionCount);
        Assert.True(plugin.TryGetFunction("SelectTestEntityRecords", out _));
    }

    [Fact]
    public void CreateInsertFunctionWithoutInputMapperThrowsNotSupportedException()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(
            () => service.CreateInsertFunction<TestDbContext, TestEntity>());
    }

    [Fact]
    public void CreateUpdateFunctionWithoutScopedResolverThrowsNotSupportedException()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(
            () => service.CreateUpdateFunction<TestDbContext, TestEntity>());
    }

    [Fact]
    public void CreateDeleteFunctionWithoutScopedResolverThrowsNotSupportedException()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(
            () => service.CreateDeleteFunction<TestDbContext, TestEntity>());
    }

    [Fact]
    public void CreateStructuredDataPluginWithMutationThrowsNotSupportedException()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(
            () => StructuredDataPluginFactory.CreateStructuredDataPlugin<TestDbContext, TestEntity>(
                service,
                [StructuredDataOperation.Insert]));
    }

    [Fact]
    public async Task CreateInsertFunctionUsesApplicationMapperAsync()
    {
        // Arrange
        TestEntity? insertedEntity = null;
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        mockSet
            .Setup(set => set.Add(It.IsAny<TestEntity>()))
            .Callback<TestEntity>(entity => insertedEntity = entity)
            .Returns<TestEntity>(entity => entity);
        mockContext.Setup(context => context.Set<TestEntity>()).Returns(mockSet.Object);
        mockContext.Setup(context => context.SaveChangesAsync(It.IsAny<CancellationToken>())).ReturnsAsync(1);
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);
        var function = service.CreateInsertFunction<TestDbContext, TestEntity, InsertTestRequest>(
            input => new TestEntity
            {
                Name = input.Name,
                ServerManagedValue = "server"
            });

        // Act
        var result = await function.InvokeAsync(
            new Kernel(),
            new() { ["input"] = """{"Name":"client","ServerManagedValue":"client"}""" });

        // Assert
        Assert.NotNull(insertedEntity);
        Assert.Equal("client", insertedEntity.Name);
        Assert.Equal("server", insertedEntity.ServerManagedValue);
        Assert.Same(insertedEntity, result.GetValue<TestEntity>());
        Assert.DoesNotContain(
            nameof(TestEntity.ServerManagedValue),
            function.Metadata.Parameters.Single().Schema!.ToString(),
            StringComparison.Ordinal);
    }

    [Fact]
    public void CreateInsertFunctionRejectsPersistenceEntityInput()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(
            () => service.CreateInsertFunction<TestDbContext, TestEntity, TestEntity>(input => input));
    }

    [Fact]
    public async Task CreateUpdateFunctionRejectsEntityOutsideApplicationScopeAsync()
    {
        // Arrange
        var updatesApplied = false;
        var mockContext = new Mock<TestDbContext>("TestConnection");
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);
        var function = service.CreateUpdateFunction<TestDbContext, TestEntity, UpdateTestRequest>(
            (_, _) => Task.FromResult<TestEntity?>(null),
            (_, _) => updatesApplied = true);

        // Act
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            () => function.InvokeAsync(new Kernel(), new() { ["input"] = """{"Name":"missing"}""" }));

        // Assert
        Assert.Equal("The requested entity is not available for update.", exception.Message);
        Assert.False(updatesApplied);
        mockContext.Verify(context => context.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task CreateUpdateFunctionUsesScopedTrackedEntityAndExplicitMapperAsync()
    {
        // Arrange
        using var context = new TrackingTestDbContext();
        var entity = new TestEntity
        {
            Id = 1,
            Name = "original",
            ServerManagedValue = "server"
        };
        context.Set<TestEntity>().Attach(entity);
        using var service = new StructuredDataService<TrackingTestDbContext>(context);
        var function = service.CreateUpdateFunction<TrackingTestDbContext, TestEntity, UpdateTestRequest>(
            (input, _) => Task.FromResult<TestEntity?>(input.Name == "updated" ? entity : null),
            (input, existingEntity) => existingEntity.Name = input.Name);

        // Act
        var result = await function.InvokeAsync(
            new Kernel(),
            new() { ["input"] = """{"Name":"updated","ServerManagedValue":"client"}""" });

        // Assert
        Assert.Equal(1, result.GetValue<int>());
        Assert.Equal("updated", entity.Name);
        Assert.Equal("server", entity.ServerManagedValue);
    }

    [Fact]
    public async Task CreateUpdateFunctionRejectsDetachedResolverResultAsync()
    {
        // Arrange
        using var context = new TrackingTestDbContext();
        using var service = new StructuredDataService<TrackingTestDbContext>(context);
        var function = service.CreateUpdateFunction<TrackingTestDbContext, TestEntity, UpdateTestRequest>(
            (_, _) => Task.FromResult<TestEntity?>(new TestEntity()),
            (input, entity) => entity.Name = input.Name);

        // Act
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            () => function.InvokeAsync(new Kernel(), new() { ["input"] = """{"Name":"updated"}""" }));

        // Assert
        Assert.Equal("The update resolver must return an entity tracked by the structured data service.", exception.Message);
        Assert.Equal(0, context.SaveChangesCallCount);
    }

    [Fact]
    public async Task CreateDeleteFunctionRejectsEntityOutsideApplicationScopeAsync()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);
        var function = service.CreateDeleteFunction<TestDbContext, TestEntity, DeleteTestRequest>(
            (_, _) => Task.FromResult<TestEntity?>(null));

        // Act
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            () => function.InvokeAsync(new Kernel(), new() { ["input"] = """{"Name":"missing"}""" }));

        // Assert
        Assert.Equal("The requested entity is not available for deletion.", exception.Message);
        mockContext.Verify(context => context.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task CreateDeleteFunctionUsesScopedTrackedEntityAsync()
    {
        // Arrange
        using var context = new TrackingTestDbContext();
        var entity = new TestEntity { Id = 1, Name = "delete" };
        context.Set<TestEntity>().Attach(entity);
        using var service = new StructuredDataService<TrackingTestDbContext>(context);
        var function = service.CreateDeleteFunction<TrackingTestDbContext, TestEntity, DeleteTestRequest>(
            (input, _) => Task.FromResult<TestEntity?>(input.Name == "delete" ? entity : null));

        // Act
        var result = await function.InvokeAsync(
            new Kernel(),
            new() { ["input"] = """{"Name":"delete"}""" });

        // Assert
        Assert.Equal(1, result.GetValue<int>());
        Assert.Equal(EntityState.Deleted, context.Entry(entity).State);
        Assert.Equal(1, context.SaveChangesCallCount);
    }

    [Fact]
    public void SelectWithNoQueryReturnsAllEntities()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var entities = new[]
        {
            new TestEntity { Id = 1, Name = "Test1" },
            new TestEntity { Id = 2, Name = "Test2" }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act
        var result = service.Select<TestEntity>().ToList();

        // Assert
        Assert.Equal(2, result.Count);
    }

    [Fact]
    public async Task InsertAsyncValidEntityInsertsAndReturnsEntityAsync()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);
        var entity = new TestEntity { Name = "Test" };

        // Act
        var result = await service.InsertAsync(entity);

        // Assert
        mockSet.Verify(m => m.Add(entity), Times.Once);
        mockContext.Verify(m => m.SaveChangesAsync(default), Times.Once);
        Assert.Same(entity, result);
    }

    [Fact]
    public async Task UpdateAsyncValidEntityUpdatesAndReturnsAffectedRowsAsync()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection") { CallBase = true };
        var mockSet = new Mock<DbSet<TestEntity>>();

        // Setup OnModelCreating behavior
        mockContext.Protected()
            .Setup("OnModelCreating", ItExpr.IsAny<DbModelBuilder>())
            .Callback<DbModelBuilder>(modelBuilder =>
            {
                var mockedContextType = mockContext.Object.GetType();
                typeof(Database).GetMethod("SetInitializer")!
                    .MakeGenericMethod(mockedContextType)
                    .Invoke(null, new object?[] { null });
            });

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);
        mockContext.Setup(m => m.SaveChangesAsync(default)).ReturnsAsync(1);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);
        var entity = new TestEntity { Id = 1, Name = "Updated" };

        // Act
        var result = await service.UpdateAsync(entity);

        // Assert
        Assert.Equal(1, result);
        mockContext.Verify(m => m.SaveChangesAsync(default), Times.Once);
    }

    [Fact]
    public async Task DeleteAsyncValidEntityDeletesAndReturnsAffectedRowsAsync()
    {
        // Arrange
        var mockSet = new Mock<DbSet<TestEntity>>();
        var mockContext = new Mock<TestDbContext>("TestConnection") { CallBase = true };

        // Setup OnModelCreating behavior
        mockContext.Protected()
            .Setup("OnModelCreating", ItExpr.IsAny<DbModelBuilder>())
            .Callback<DbModelBuilder>(modelBuilder =>
            {
                Database.SetInitializer(null as System.Data.Entity.IDatabaseInitializer<TestDbContext>);
                var mockedContextType = mockContext.Object.GetType();
                typeof(Database).GetMethod("SetInitializer")!
                    .MakeGenericMethod(mockedContextType)
                    .Invoke(null, new object?[] { null });
            });

        mockSet.Setup(m => m.Remove(It.IsAny<TestEntity>())).Returns((TestEntity e) => e);
        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);
        mockContext.Setup(m => m.SaveChangesAsync(It.IsAny<System.Threading.CancellationToken>())).ReturnsAsync(1);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);
        var entity = new TestEntity { Id = 1, Name = "ToDelete" };

        // Act
        var result = await service.DeleteAsync(entity);

        // Assert
        Assert.Equal(1, result);
    }

    [Fact]
    public void SelectWithFilterQueryAppliesFilter()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var entities = new[]
        {
            new TestEntity { Id = 1, Name = "Test1" },
            new TestEntity { Id = 2, Name = "Test2" }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act
        var result = service.Select<TestEntity>("Name eq 'Test1'").ToList();

        // Assert
        Assert.Single(result);
        Assert.Equal("Test1", result[0].Name);
    }

    [Fact]
    public void SelectWithDateTimeFilterQueryHandlesNullableAndNonNullable()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var testDate = new DateTime(2023, 1, 1, 0, 0, 0, DateTimeKind.Utc);
        var entities = new[]
        {
            new TestEntity { Id = 1, Name = "Test1", NullableDate = testDate },
            new TestEntity { Id = 2, Name = "Test2", NullableDate = null },
            new TestEntity { Id = 3, Name = "Test3", NullableDate = testDate.AddDays(1) }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        // Test exact date match with non-null value
        var result1 = service.Select<TestEntity>($"NullableDate eq {testDate:yyyy-MM-ddTHH:mm:ssZ}").ToList();
        Assert.Single(result1);
        Assert.Equal(1, result1[0].Id);

        // Test null handling
        var result2 = service.Select<TestEntity>("NullableDate eq null").ToList();
        Assert.Single(result2);
        Assert.Equal(2, result2[0].Id);

        // Test greater than comparison
        var result3 = service.Select<TestEntity>($"NullableDate gt {testDate:yyyy-MM-ddTHH:mm:ssZ}").ToList();
        Assert.Single(result3);
        Assert.Equal(3, result3[0].Id);
    }

    [Fact]
    public void SelectWithDateTimeFilterQueryHandlesMultipleConditions()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var testDate = new DateTime(2023, 1, 1, 0, 0, 0, DateTimeKind.Utc);
        var entities = new[]
        {
            new TestEntity { Id = 1, Name = "Test1", NullableDate = testDate },
            new TestEntity { Id = 2, Name = "Test2", NullableDate = null },
            new TestEntity { Id = 3, Name = "Test3", NullableDate = testDate }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        // Test combination of date and string conditions
        var result = service.Select<TestEntity>($"NullableDate eq {testDate:yyyy-MM-ddTHH:mm:ssZ} and Name eq 'Test1'").ToList();
        Assert.Single(result);
        Assert.Equal(1, result[0].Id);

        // Test OR condition with null
        var result2 = service.Select<TestEntity>("NullableDate eq null or Name eq 'Test3'").ToList();
        Assert.Equal(2, result2.Count);
        Assert.Contains(result2, e => e.Id == 2);
        Assert.Contains(result2, e => e.Id == 3);
    }

    [Theory]
    [InlineData("2023-01-01T00:00:00Z")]
    [InlineData("2023-01-01T00:00:00.000Z")]
    public void SelectWithDateTimeFilterHandlesVariousDateFormats(string dateFormat)
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var testDate = new DateTime(2023, 1, 1, 0, 0, 0, DateTimeKind.Utc);
        var entities = new[]
        {
            new TestEntity { Id = 1, NullableDate = testDate },
            new TestEntity { Id = 2, NullableDate = testDate.AddDays(1) }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act
        var result = service.Select<TestEntity>($"NullableDate eq {dateFormat}").ToList();

        // Assert
        Assert.Single(result);
        Assert.Equal(1, result[0].Id);
    }

    [Fact]
    public void SelectWithNullableTypesHandlesComparisons()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var entities = new[]
        {
            new TestEntity { Id = 1, NullableInt = 10, NullableDouble = 1.5, NullableBool = true },
            new TestEntity { Id = 2, NullableInt = null, NullableDouble = null, NullableBool = null },
            new TestEntity { Id = 3, NullableInt = 20, NullableDouble = 2.5, NullableBool = false }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        // Test nullable int
        var result1 = service.Select<TestEntity>("NullableInt eq 10").ToList();
        Assert.Single(result1);
        Assert.Equal(1, result1[0].Id);

        // Test nullable double
        var result2 = service.Select<TestEntity>("NullableDouble gt 2.0").ToList();
        Assert.Single(result2);
        Assert.Equal(3, result2[0].Id);

        // Test nullable bool
        var result3 = service.Select<TestEntity>("NullableBool eq true").ToList();
        Assert.Single(result3);
        Assert.Equal(1, result3[0].Id);

        // Test null values
        var result4 = service.Select<TestEntity>("NullableInt eq null").ToList();
        Assert.Single(result4);
        Assert.Equal(2, result4[0].Id);

        // Test complex condition
        var result5 = service.Select<TestEntity>("NullableInt gt 15 and NullableBool eq false").ToList();
        Assert.Single(result5);
        Assert.Equal(3, result5[0].Id);
    }

    [Theory]
    [InlineData("eq", 10, 1)]
    [InlineData("ne", 10, 2)]
    [InlineData("gt", 15, 1)]
    [InlineData("lt", 15, 1)]
    [InlineData("ge", 20, 1)]
    [InlineData("le", 10, 1)]
    public void SelectWithNullableTypesHandlesAllOperators(string op, int value, int expectedCount)
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var entities = new[]
        {
            new TestEntity { Id = 1, NullableInt = 10 },
            new TestEntity { Id = 2, NullableInt = null },
            new TestEntity { Id = 3, NullableInt = 20 }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act
        var result = service.Select<TestEntity>($"NullableInt {op} {value}").ToList();

        // Assert
        Assert.Equal(expectedCount, result.Count);
    }

    [Fact]
    public void SelectWithQuotedStringHandlesSpacesCorrectly()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var entities = new[]
        {
            new TestEntity { Id = 1, Name = "Sample Product" },
            new TestEntity { Id = 2, Name = "Another Product" }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        // Test single quotes
        var result1 = service.Select<TestEntity>("Name eq 'Sample Product'").ToList();
        Assert.Single(result1);
        Assert.Equal("Sample Product", result1[0].Name);
    }

    [Fact]
    public void SelectWithQuotedStringHandlesComplexQueries()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var entities = new[]
        {
            new TestEntity { Id = 1, Name = "Product with and", NullableDouble = 10 },
            new TestEntity { Id = 2, Name = "Product or test", NullableDouble = 20 },
            new TestEntity { Id = 3, Name = "Simple Product", NullableDouble = 30 }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        // Test string containing 'and'
        var result1 = service.Select<TestEntity>("Name eq 'Product with and'").ToList();
        Assert.Single(result1);
        Assert.Equal("Product with and", result1[0].Name);

        // Test complex condition with quoted string and numeric comparison
        var result2 = service.Select<TestEntity>("Name eq 'Product with and' and NullableDouble lt 15").ToList();
        Assert.Single(result2);
        Assert.Equal(10, result2[0].NullableDouble);

        // Test OR condition with quoted strings
        var result3 = service.Select<TestEntity>("Name eq 'Product with and' or Name eq 'Product or test'").ToList();
        Assert.Equal(2, result3.Count);
        Assert.Contains(result3, e => e.Name == "Product with and");
        Assert.Contains(result3, e => e.Name == "Product or test");
    }

    [Fact]
    public void SelectWithQuotedStringHandlesEscapedQuotes()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        var entities = new[]
        {
            new TestEntity { Id = 1, Name = "Product's Test" },
            new TestEntity { Id = 2, Name = "Product \"Quote\" Test" }
        }.AsQueryable();

        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Provider).Returns(entities.Provider);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.Expression).Returns(entities.Expression);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.ElementType).Returns(entities.ElementType);
        mockSet.As<IQueryable<TestEntity>>().Setup(m => m.GetEnumerator()).Returns(entities.GetEnumerator());

        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);

        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);

        // Act & Assert
        // Test string with single quote
        var result1 = service.Select<TestEntity>("Name eq 'Product''s Test'").ToList();
        Assert.Single(result1);
        Assert.Equal("Product's Test", result1[0].Name);

        // Test string with double quotes
        var result2 = service.Select<TestEntity>(@"Name eq 'Product ""Quote"" Test'").ToList();
        Assert.Single(result2);
        Assert.Equal("Product \"Quote\" Test", result2[0].Name);
    }

    public class TestEntity
    {
        public int Id { get; set; }
        public string? Name { get; set; }
        public string? ServerManagedValue { get; set; }

        public DateTimeOffset? NullableDate { get; set; }
        public int? NullableInt { get; set; }
        public double? NullableDouble { get; set; }
        public bool? NullableBool { get; set; }
    }

    public sealed class InsertTestRequest
    {
        public string? Name { get; set; }
    }

    public sealed class UpdateTestRequest
    {
        public string? Name { get; set; }
    }

    public sealed class DeleteTestRequest
    {
        public string? Name { get; set; }
    }

    public class TestDbContext : DbContext
    {
        public TestDbContext(string nameOrConnectionString) : base(nameOrConnectionString)
        {
            // Disable database initialization for unit tests
            Database.SetInitializer<TestDbContext>(null);
        }

        protected override void OnModelCreating(DbModelBuilder modelBuilder)
        {
            Database.SetInitializer<TestDbContext>(null);
            base.OnModelCreating(modelBuilder);
        }
        public virtual void Entry<TEntity>(TEntity entity, Action<DbEntityEntry<TEntity>> action) where TEntity : class
        {
            action(base.Entry(entity));
        }

        [Obsolete("Use overload for unit tests.")]
        public new DbEntityEntry<TEntity> Entry<TEntity>(TEntity entity) where TEntity : class
        {
            throw new NotSupportedException("Use overload for unit tests.");
        }

        public DbSet<TestEntity>? TestEntities { get; set; }
    }

    public sealed class TrackingTestDbContext : DbContext
    {
        public TrackingTestDbContext() : base("TestConnection")
        {
            Database.SetInitializer<TrackingTestDbContext>(null);
        }

        public int SaveChangesCallCount { get; private set; }

        public DbSet<TestEntity>? TestEntities { get; set; }

        public override Task<int> SaveChangesAsync(CancellationToken cancellationToken)
        {
            this.SaveChangesCallCount++;
            return Task.FromResult(1);
        }
    }
}
