// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;
using Xunit;

namespace VectorData.UnitTests;

public class TelemetryHelpersTests
{
    [Fact]
    public async Task RunOperationWithoutResultWorksWithActivityAndMetricsAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();

        var operationName = "test_operation";
        var collectionName = "testcollection";
        var databaseName = "testdb";
        var systemName = "testsystem";

        using var activitySource = new ActivitySource(sourceName);
        using var meter = new Meter(sourceName);
        var histogram = meter.CreateHistogram<double>("db.client.operation.duration", "s", "Duration of database client operations");

        var activities = new List<Activity>();
        var metrics = new List<Metric>();

        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        using var meterProvider = OpenTelemetry.Sdk.CreateMeterProviderBuilder()
            .AddMeter(sourceName)
            .AddInMemoryExporter(metrics)
            .Build();

        bool operationExecuted = false;
        async Task Operation()
        {
            await Task.Yield();
            operationExecuted = true;
        }

        // Act
        await TelemetryHelpers.RunOperationAsync(
            activitySource,
            operationName,
            collectionName,
            databaseName,
            systemName,
            histogram,
            Operation);

        // Assert
        Assert.True(operationExecuted);

        var activity = Assert.Single(activities);

        Assert.Equal($"{operationName} {collectionName}", activity.DisplayName);
        Assert.Equal(operationName, activity.GetTagItem("db.operation.name"));
        Assert.Equal(collectionName, activity.GetTagItem("db.collection.name"));
        Assert.Equal(databaseName, activity.GetTagItem("db.namespace"));
        Assert.Equal(systemName, activity.GetTagItem("db.system.name"));

        // Force metrics to be collected
        meterProvider.ForceFlush(timeoutMilliseconds: 1000);

        var metric = Assert.Single(metrics);

        Assert.Equal("db.client.operation.duration", metric.Name);

        this.AssertMetric(metric, operationName);
    }

    [Fact]
    public async Task RunOperationWithoutResultRecordsErrorOnExceptionAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var operationName = "test_operation";
        var collectionName = "testcollection";
        var databaseName = "testdb";
        var systemName = "testsystem";

        using var activitySource = new ActivitySource(sourceName);
        using var meter = new Meter(sourceName);
        var histogram = meter.CreateHistogram<double>("db.client.operation.duration", "s", "Duration of database client operations");

        var activities = new List<Activity>();
        var metrics = new List<Metric>();

        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        using var meterProvider = OpenTelemetry.Sdk.CreateMeterProviderBuilder()
            .AddMeter(sourceName)
            .AddInMemoryExporter(metrics)
            .Build();

        static Task Operation() => throw new InvalidOperationException("Test exception");

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            TelemetryHelpers.RunOperationAsync(
                activitySource,
                operationName,
                collectionName,
                databaseName,
                systemName,
                histogram,
                Operation));

        Assert.Equal("Test exception", exception.Message);

        var activity = Assert.Single(activities);

        Assert.Equal(ActivityStatusCode.Error, activity.Status);
        Assert.Equal(typeof(InvalidOperationException).FullName, activity.GetTagItem("error.type"));

        // Force metrics to be collected
        meterProvider.ForceFlush(timeoutMilliseconds: 1000);

        var metric = Assert.Single(metrics);

        this.AssertMetricError(metric);
    }

    [Fact]
    public async Task RunOperationWithResultWorksWithActivityAndMetricsAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var operationName = "test_operation";
        var collectionName = "testcollection";
        var databaseName = "testdb";
        var systemName = "testsystem";

        using var activitySource = new ActivitySource(sourceName);
        using var meter = new Meter(sourceName);
        var histogram = meter.CreateHistogram<double>("db.client.operation.duration", "s", "Duration of database client operations");

        var activities = new List<Activity>();
        var metrics = new List<Metric>();

        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        using var meterProvider = OpenTelemetry.Sdk.CreateMeterProviderBuilder()
            .AddMeter(sourceName)
            .AddInMemoryExporter(metrics)
            .Build();

        async static Task<int> Operation()
        {
            await Task.Yield();
            return 42;
        }

        // Act
        var result = await TelemetryHelpers.RunOperationAsync(
            activitySource,
            operationName,
            collectionName,
            databaseName,
            systemName,
            histogram,
            Operation);

        // Assert
        Assert.Equal(42, result);

        var activity = Assert.Single(activities);
        Assert.Equal($"{operationName} {collectionName}", activity.DisplayName);
        Assert.Equal(operationName, activity.GetTagItem("db.operation.name"));
        Assert.Equal(collectionName, activity.GetTagItem("db.collection.name"));
        Assert.Equal(databaseName, activity.GetTagItem("db.namespace"));
        Assert.Equal(systemName, activity.GetTagItem("db.system.name"));

        // Force metrics to be collected
        meterProvider.ForceFlush(timeoutMilliseconds: 1000);

        var metric = Assert.Single(metrics);

        Assert.Equal("db.client.operation.duration", metric.Name);

        this.AssertMetric(metric, operationName);
    }

    [Fact]
    public async Task RunOperationWithResultRecordsErrorOnExceptionAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var operationName = "test_operation";
        var collectionName = "testcollection";
        var databaseName = "testdb";
        var systemName = "testsystem";

        using var activitySource = new ActivitySource(sourceName);
        using var meter = new Meter(sourceName);
        var histogram = meter.CreateHistogram<double>("db.client.operation.duration", "s", "Duration of database client operations");

        var activities = new List<Activity>();
        var metrics = new List<Metric>();

        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        using var meterProvider = OpenTelemetry.Sdk.CreateMeterProviderBuilder()
            .AddMeter(sourceName)
            .AddInMemoryExporter(metrics)
            .Build();

        static Task<int> Operation() => throw new InvalidOperationException("Test exception");

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            TelemetryHelpers.RunOperationAsync(
                activitySource,
                operationName,
                collectionName,
                databaseName,
                systemName,
                histogram,
                Operation));

        Assert.Equal("Test exception", exception.Message);

        var activity = Assert.Single(activities);

        Assert.Equal(ActivityStatusCode.Error, activity.Status);
        Assert.Equal(typeof(InvalidOperationException).FullName, activity.GetTagItem("error.type"));

        // Force metrics to be collected
        meterProvider.ForceFlush(timeoutMilliseconds: 1000);

        var metric = Assert.Single(metrics);

        this.AssertMetricError(metric);
    }

    [Fact]
    public async Task RunOperationWithAsyncEnumerableWorksWithActivityAndMetricsAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var result = new[] { 1, 2, 3 };

        var operationName = "test_operation";
        var collectionName = "testcollection";
        var databaseName = "testdb";
        var systemName = "testsystem";

        using var activitySource = new ActivitySource(sourceName);
        using var meter = new Meter(sourceName);
        var histogram = meter.CreateHistogram<double>("db.client.operation.duration", "s", "Duration of database client operations");

        var activities = new List<Activity>();
        var metrics = new List<Metric>();

        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        using var meterProvider = OpenTelemetry.Sdk.CreateMeterProviderBuilder()
            .AddMeter(sourceName)
            .AddInMemoryExporter(metrics)
            .Build();

        IAsyncEnumerable<int> Operation()
        {
            return result.ToAsyncEnumerable();
        }

        // Act
        var results = await TelemetryHelpers.RunOperationAsync(
            activitySource,
            operationName,
            collectionName,
            databaseName,
            systemName,
            histogram,
            Operation,
            default).ToListAsync();

        // Assert
        Assert.Equal(result, results);

        var activity = Assert.Single(activities);

        Assert.Equal($"{operationName} {collectionName}", activity.DisplayName);
        Assert.Equal(operationName, activity.GetTagItem("db.operation.name"));
        Assert.Equal(collectionName, activity.GetTagItem("db.collection.name"));
        Assert.Equal(databaseName, activity.GetTagItem("db.namespace"));
        Assert.Equal(systemName, activity.GetTagItem("db.system.name"));

        // Force metrics to be collected
        meterProvider.ForceFlush(timeoutMilliseconds: 1000);

        var metric = Assert.Single(metrics);

        Assert.Equal("db.client.operation.duration", metric.Name);

        this.AssertMetric(metric, operationName);
    }

    [Fact]
    public async Task RunOperationWithAsyncEnumerableRecordsErrorOnExceptionDuringEnumerationAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var operationName = "test_operation";
        var collectionName = "testcollection";
        var databaseName = "testdb";
        var systemName = "testsystem";

        using var activitySource = new ActivitySource(sourceName);
        using var meter = new Meter(sourceName);
        var histogram = meter.CreateHistogram<double>("db.client.operation.duration", "s", "Duration of database client operations");

        var activities = new List<Activity>();
        var metrics = new List<Metric>();

        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        using var meterProvider = OpenTelemetry.Sdk.CreateMeterProviderBuilder()
            .AddMeter(sourceName)
            .AddInMemoryExporter(metrics)
            .Build();

        async static IAsyncEnumerable<int> Operation()
        {
            yield return 1;
            await Task.Yield();
            throw new InvalidOperationException("Test exception");
        }

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await TelemetryHelpers.RunOperationAsync(
                activitySource,
                operationName,
                collectionName,
                databaseName,
                systemName,
                histogram,
                Operation,
                default).ToListAsync());

        Assert.Equal("Test exception", exception.Message);

        var activity = Assert.Single(activities);

        Assert.Equal(ActivityStatusCode.Error, activity.Status);
        Assert.Equal(typeof(InvalidOperationException).FullName, activity.GetTagItem("error.type"));

        // Force metrics to be collected
        meterProvider.ForceFlush(timeoutMilliseconds: 1000);

        var metric = Assert.Single(metrics);

        this.AssertMetricError(metric);
    }

    #region private

    private void AssertMetric(Metric? metric, string operationName)
    {
        var metricExists = false;

        if (metric is not null)
        {
            foreach (var point in metric.GetMetricPoints())
            {
                var histogramExists = point.GetHistogramSum() > 0;
                var tagExists = false;

                foreach (var tag in point.Tags)
                {
                    if (tag.Key == "db.operation.name" && tag.Value?.ToString() == operationName)
                    {
                        tagExists = true;
                    }
                }

                metricExists = histogramExists && tagExists;
            }
        }

        Assert.True(metricExists);
    }

    private void AssertMetricError(Metric? metric)
    {
        var metricErrorExists = false;

        if (metric is not null)
        {
            foreach (var point in metric.GetMetricPoints())
            {
                foreach (var tag in point.Tags)
                {
                    metricErrorExists =
                        tag.Key == "error.type" &&
                        tag.Value?.ToString() == typeof(InvalidOperationException).FullName;
                }
            }
        }

        Assert.True(metricErrorExists);
    }

    #endregion
}
