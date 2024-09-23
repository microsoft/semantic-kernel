// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;
using Moq;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.MsGraph;

public class CalendarSkillTests
{
    [Fact]
    public async Task AddEventAsyncSucceedsAsync()
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();
        string anyLocation = Guid.NewGuid().ToString();
        DateTimeOffset anyStartTime = DateTimeOffset.Now + TimeSpan.FromDays(1);
        DateTimeOffset anyEndTime = DateTimeOffset.Now + TimeSpan.FromDays(1.1);
        string[] anyAttendees = new[] { Guid.NewGuid().ToString(), Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };

        CalendarEvent expected = new()
        {
            Subject = anySubject,
            Location = anyLocation,
            Attendees = anyAttendees
        };

        Mock<ICalendarConnector> connectorMock = new();
        connectorMock.Setup(c => c.AddEventAsync(It.IsAny<CalendarEvent>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        CalendarSkill target = new(connectorMock.Object);

        // Act
        var context = await FunctionHelpers.CallViaKernel(target, "AddEvent",
            ("input", anySubject),
            ("start", anyStartTime.ToString(CultureInfo.InvariantCulture)),
            ("end", anyEndTime.ToString(CultureInfo.InvariantCulture)),
            ("location", anyLocation),
            ("content", anyContent),
            ("attendees", string.Join(";", anyAttendees)));

        // Assert
        Assert.False(context.ErrorOccurred);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task AddEventAsyncWithoutLocationSucceedsAsync()
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();
        DateTimeOffset anyStartTime = DateTimeOffset.Now + TimeSpan.FromDays(1);
        DateTimeOffset anyEndTime = DateTimeOffset.Now + TimeSpan.FromDays(1.1);
        string[] anyAttendees = new[] { Guid.NewGuid().ToString(), Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };

        CalendarEvent expected = new()
        {
            Content = anyContent,
            Subject = anySubject,
            Attendees = anyAttendees,
            Start = anyStartTime,
            End = anyEndTime
        };

        Mock<ICalendarConnector> connectorMock = new();
        connectorMock.Setup(c => c.AddEventAsync(It.IsAny<CalendarEvent>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        CalendarSkill target = new(connectorMock.Object);

        // Act
        var context = await FunctionHelpers.CallViaKernel(target, "AddEvent",
            ("input", anySubject),
            ("start", anyStartTime.ToString(CultureInfo.InvariantCulture)),
            ("end", anyEndTime.ToString(CultureInfo.InvariantCulture)),
            ("content", anyContent),
            ("attendees", string.Join(";", anyAttendees)));

        // Assert
        Assert.False(context.ErrorOccurred);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task AddEventAsyncWithoutContentSucceedsAsync()
    {
        // Arrange
        string anySubject = Guid.NewGuid().ToString();
        string anyLocation = Guid.NewGuid().ToString();
        DateTimeOffset anyStartTime = DateTimeOffset.Now + TimeSpan.FromDays(1);
        DateTimeOffset anyEndTime = DateTimeOffset.Now + TimeSpan.FromDays(1.1);
        string[] anyAttendees = new[] { Guid.NewGuid().ToString(), Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };

        CalendarEvent expected = new()
        {
            Subject = anySubject,
            Start = anyStartTime,
            End = anyEndTime,
            Location = anyLocation,
            Attendees = anyAttendees
        };

        Mock<ICalendarConnector> connectorMock = new();
        connectorMock.Setup(c => c.AddEventAsync(It.IsAny<CalendarEvent>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        CalendarSkill target = new(connectorMock.Object);

        // Act
        var context = await FunctionHelpers.CallViaKernel(target, "AddEvent",
            ("input", anySubject),
            ("start", anyStartTime.ToString(CultureInfo.InvariantCulture)),
            ("end", anyEndTime.ToString(CultureInfo.InvariantCulture)),
            ("location", anyLocation),
            ("attendees", string.Join(";", anyAttendees)));

        // Assert
        Assert.False(context.ErrorOccurred);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task AddEventAsyncWithoutAttendeesSucceedsAsync()
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();
        string anyLocation = Guid.NewGuid().ToString();
        DateTimeOffset anyStartTime = DateTimeOffset.Now + TimeSpan.FromDays(1);
        DateTimeOffset anyEndTime = DateTimeOffset.Now + TimeSpan.FromDays(1.1);

        CalendarEvent expected = new()
        {
            Subject = anySubject,
            Start = anyStartTime,
            End = anyEndTime,
            Content = anyContent,
            Location = anyLocation
        };

        Mock<ICalendarConnector> connectorMock = new();
        connectorMock.Setup(c => c.AddEventAsync(It.IsAny<CalendarEvent>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        CalendarSkill target = new(connectorMock.Object);

        // Act
        var context = await FunctionHelpers.CallViaKernel(target, "AddEvent",
            ("input", anySubject),
            ("start", anyStartTime.ToString(CultureInfo.InvariantCulture)),
            ("end", anyEndTime.ToString(CultureInfo.InvariantCulture)),
            ("location", anyLocation),
            ("content", anyContent));

        // Assert
        Assert.False(context.ErrorOccurred);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task AddEventAsyncWithoutStartFailsAsync()
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();
        string anyLocation = Guid.NewGuid().ToString();
        DateTimeOffset anyEndTime = DateTimeOffset.Now + TimeSpan.FromDays(1.1);
        string[] anyAttendees = new[] { Guid.NewGuid().ToString(), Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };

        Mock<ICalendarConnector> connectorMock = new();

        CalendarSkill target = new(connectorMock.Object);

        // Act
        var context = await FunctionHelpers.CallViaKernel(target, "AddEvent",
            ("input", anySubject),
            ("end", anyEndTime.ToString(CultureInfo.InvariantCulture)),
            ("location", anyLocation),
            ("content", anyContent),
            ("attendees", string.Join(";", anyAttendees)));

        // Assert
        Assert.True(context.ErrorOccurred);
        Assert.IsType<SKException>(context.LastException);
    }

    [Fact]
    public async Task AddEventAsyncWithoutEndFailsAsync()
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();
        string anyLocation = Guid.NewGuid().ToString();
        DateTimeOffset anyStartTime = DateTimeOffset.Now + TimeSpan.FromDays(1);
        string[] anyAttendees = new[] { Guid.NewGuid().ToString(), Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };

        Mock<ICalendarConnector> connectorMock = new();

        CalendarSkill target = new(connectorMock.Object);

        // Act
        var context = await FunctionHelpers.CallViaKernel(target, "AddEvent",
            ("input", anySubject),
            ("start", anyStartTime.ToString(CultureInfo.InvariantCulture)),
            ("location", anyLocation),
            ("content", anyContent),
            ("attendees", string.Join(";", anyAttendees)));

        // Assert
        Assert.True(context.ErrorOccurred);
        Assert.IsType<SKException>(context.LastException);
    }

    [Fact]
    public async Task AddEventAsyncWithoutSubjectFailsAsync()
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        string anyLocation = Guid.NewGuid().ToString();
        DateTimeOffset anyStartTime = DateTimeOffset.Now + TimeSpan.FromDays(1);
        DateTimeOffset anyEndTime = DateTimeOffset.Now + TimeSpan.FromDays(1.1);
        string[] anyAttendees = new[] { Guid.NewGuid().ToString(), Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };

        Mock<ICalendarConnector> connectorMock = new();

        CalendarSkill target = new(connectorMock.Object);

        // Act
        var context = await FunctionHelpers.CallViaKernel(target, "AddEvent",
            ("start", anyStartTime.ToString(CultureInfo.InvariantCulture)),
            ("end", anyEndTime.ToString(CultureInfo.InvariantCulture)),
            ("location", anyLocation),
            ("content", anyContent),
            ("attendees", string.Join(";", anyAttendees)));

        // Assert
        Assert.True(context.ErrorOccurred);
        ArgumentException e = Assert.IsType<ArgumentException>(context.LastException);
        Assert.Equal("subject", e.ParamName);
    }
}
