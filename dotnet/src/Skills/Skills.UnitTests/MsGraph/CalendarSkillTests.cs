// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;
using Moq;
using SemanticKernel.Skills.UnitTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;
using static Microsoft.SemanticKernel.Skills.MsGraph.CalendarSkill;

namespace SemanticKernel.Skills.UnitTests.MsGraph;

public class CalendarSkillTests : IDisposable
{
    private readonly XunitLogger<SKContext> _logger;
    private readonly SKContext _context;

    public CalendarSkillTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<SKContext>(output);
        this._context = new SKContext(logger: this._logger);
    }

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

        this._context.Variables.Set(Parameters.Start, anyStartTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.End, anyEndTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.Location, anyLocation);
        this._context.Variables.Set(Parameters.Content, anyContent);
        this._context.Variables.Set(Parameters.Attendees, string.Join(";", anyAttendees));

        // Act
        await target.AddEventAsync(anySubject, this._context);

        // Assert
        Assert.False(this._context.ErrorOccurred);
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

        this._context.Variables.Set(Parameters.Start, anyStartTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.End, anyEndTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.Content, anyContent);
        this._context.Variables.Set(Parameters.Attendees, string.Join(";", anyAttendees));

        // Act
        await target.AddEventAsync(anySubject, this._context);

        // Assert
        Assert.False(this._context.ErrorOccurred);
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

        this._context.Variables.Set(Parameters.Start, anyStartTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.End, anyEndTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.Location, anyLocation);
        this._context.Variables.Set(Parameters.Attendees, string.Join(";", anyAttendees));

        // Act
        await target.AddEventAsync(anySubject, this._context);

        // Assert
        Assert.False(this._context.ErrorOccurred);
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

        this._context.Variables.Set(Parameters.Start, anyStartTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.End, anyEndTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.Location, anyLocation);
        this._context.Variables.Set(Parameters.Content, anyContent);

        // Act
        await target.AddEventAsync(anySubject, this._context);

        // Assert
        Assert.False(this._context.ErrorOccurred);
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

        this._context.Variables.Set(Parameters.End, anyEndTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.Location, anyLocation);
        this._context.Variables.Set(Parameters.Content, anyContent);
        this._context.Variables.Set(Parameters.Attendees, string.Join(";", anyAttendees));

        // Act
        await target.AddEventAsync(anySubject, this._context);

        // Assert
        Assert.True(this._context.ErrorOccurred);
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

        this._context.Variables.Set(Parameters.Start, anyStartTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.Location, anyLocation);
        this._context.Variables.Set(Parameters.Content, anyContent);
        this._context.Variables.Set(Parameters.Attendees, string.Join(";", anyAttendees));

        // Act
        await target.AddEventAsync(anySubject, this._context);

        // Assert
        Assert.True(this._context.ErrorOccurred);
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

        this._context.Variables.Set(Parameters.Start, anyStartTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.End, anyEndTime.ToString(CultureInfo.InvariantCulture.DateTimeFormat));
        this._context.Variables.Set(Parameters.Location, anyLocation);
        this._context.Variables.Set(Parameters.Content, anyContent);
        this._context.Variables.Set(Parameters.Attendees, string.Join(";", anyAttendees));

        // Act
        await target.AddEventAsync(string.Empty, this._context);

        // Assert
        Assert.True(this._context.ErrorOccurred);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._logger.Dispose();
        }
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
