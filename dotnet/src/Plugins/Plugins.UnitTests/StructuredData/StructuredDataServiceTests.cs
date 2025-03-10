// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Data.Entity;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Moq;
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
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);
        mockContext.Setup(m => m.SaveChangesAsync(default)).ReturnsAsync(1);
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);
        var entity = new TestEntity { Id = 1, Name = "Updated" };

        // Act
        var result = await service.UpdateAsync(entity);

        // Assert
        Assert.Equal(1, result);
    }

    [Fact]
    public async Task DeleteAsyncValidEntityDeletesAndReturnsAffectedRowsAsync()
    {
        // Arrange
        var mockContext = new Mock<TestDbContext>("TestConnection");
        var mockSet = new Mock<DbSet<TestEntity>>();
        mockContext.Setup(c => c.Set<TestEntity>()).Returns(mockSet.Object);
        mockContext.Setup(m => m.SaveChangesAsync(default)).ReturnsAsync(1);
        using var service = new StructuredDataService<TestDbContext>(mockContext.Object);
        var entity = new TestEntity { Id = 1, Name = "ToDelete" };

        // Act
        var result = await service.DeleteAsync(entity);

        // Assert
        mockSet.Verify(m => m.Remove(entity), Times.Once);
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

    public sealed class TestEntity
    {
        public int? Id { get; set; }
        public string? Name { get; set; }
        public DateTime? CreatedDate { get; set; }
    }

    public class TestDbContext : DbContext
    {
        public TestDbContext(string connectionString) : base(connectionString) { }
        public DbSet<TestEntity>? TestEntities { get; set; }
    }
}
