// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.VisualBasic;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi.Serialization;

public class OpenApiTypeConverterTests
{
    [Fact]
    public void ItShouldConvertString()
    {
        // Arrange
        object? value = "test";

        // Act
        var result = OpenApiTypeConverter.Convert("id", RestApiParameterType.String, value);

        // Assert
        Assert.Equal("\"test\"", result.ToString());
    }

    [Fact]
    public void ItShouldConvertNumber()
    {
        // Act & Assert
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (byte)10).ToString());
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (sbyte)10).ToString());

        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (short)10).ToString());
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (ushort)10).ToString());

        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (int)10).ToString());
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (uint)10).ToString());

        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (long)10).ToString());
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (ulong)10).ToString());

        Assert.Equal("10.5", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (float)10.5).ToString());
        Assert.Equal("10.5", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (double)10.5).ToString());
        Assert.Equal("10.5", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, (decimal)10.5).ToString());

        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, "10").ToString());
        Assert.Equal("10.5", OpenApiTypeConverter.Convert("id", RestApiParameterType.Number, "10.5").ToString());
    }

    [Fact]
    public void ItShouldConvertInteger()
    {
        // Act & Assert
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, (byte)10).ToString());
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, (sbyte)10).ToString());

        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, (short)10).ToString());
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, (ushort)10).ToString());

        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, (int)10).ToString());
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, (uint)10).ToString());

        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, (long)10).ToString());
        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, (ulong)10).ToString());

        Assert.Equal("10", OpenApiTypeConverter.Convert("id", RestApiParameterType.Integer, "10").ToString());
    }

    [Fact]
    public void ItShouldConvertBoolean()
    {
        // Act & Assert
        Assert.Equal("true", OpenApiTypeConverter.Convert("id", RestApiParameterType.Boolean, true).ToString());

        Assert.Equal("false", OpenApiTypeConverter.Convert("id", RestApiParameterType.Boolean, false).ToString());

        Assert.Equal("true", OpenApiTypeConverter.Convert("id", RestApiParameterType.Boolean, "true").ToString());

        Assert.Equal("false", OpenApiTypeConverter.Convert("id", RestApiParameterType.Boolean, "false").ToString());
    }

    [Fact]
    public void ItShouldConvertDateTime()
    {
        // Arrange
        var dateTime = DateTime.ParseExact("06.12.2023 11:53:36+02:00", "dd.MM.yyyy HH:mm:sszzz", CultureInfo.InvariantCulture, DateTimeStyles.AdjustToUniversal);

        // Act & Assert
        Assert.Equal("\"2023-12-06T09:53:36Z\"", OpenApiTypeConverter.Convert("id", RestApiParameterType.String, dateTime).ToString());
    }

    [Fact]
    public void ItShouldConvertDateTimeOffset()
    {
        // Arrange
        var offset = DateTimeOffset.ParseExact("06.12.2023 11:53:36 +02:00", "dd.MM.yyyy HH:mm:ss zzz", CultureInfo.InvariantCulture);

        // Act & Assert
        Assert.Equal("\"2023-12-06T11:53:36+02:00\"", OpenApiTypeConverter.Convert("id", RestApiParameterType.String, offset).ToString());
    }

    [Fact]
    public void ItShouldConvertCollections()
    {
        // Act & Assert
        Assert.Equal("[1,2,3]", OpenApiTypeConverter.Convert("id", RestApiParameterType.Array, new[] { 1, 2, 3 }).ToJsonString());

        Assert.Equal("[1,2,3]", OpenApiTypeConverter.Convert("id", RestApiParameterType.Array, new List<int> { 1, 2, 3 }).ToJsonString());

        Assert.Equal("[1,2,3]", OpenApiTypeConverter.Convert("id", RestApiParameterType.Array, new Collection() { 1, 2, 3 }).ToJsonString());

        Assert.Equal("[1,2,3]", OpenApiTypeConverter.Convert("id", RestApiParameterType.Array, "[1, 2, 3]").ToJsonString());
    }
}
