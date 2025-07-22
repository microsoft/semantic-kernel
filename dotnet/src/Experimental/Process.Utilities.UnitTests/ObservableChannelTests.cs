// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Internal;
using Xunit;

namespace SemanticKernel.Process.Utilities.UnitTests;

public class ObservableChannelTests
{
    private static readonly KernelProcessEvent s_testEvent1 = new() { Data = "someData1", Id = "myId1", Visibility = KernelProcessEventVisibility.Public };
    private static readonly KernelProcessEvent s_testEvent2 = new() { Data = "someData2", Id = "myId2", Visibility = KernelProcessEventVisibility.Public };
    private static readonly KernelProcessEvent s_testEvent3 = new() { Data = "someData3", Id = "myId3", Visibility = KernelProcessEventVisibility.Public };

    [Fact]
    public async Task VerifyAfterAddingWithWriteAsyncItemsGetSnapshotAsync()
    {
        // Arrange
        var observableChannel = new ObservableChannel<KernelProcessEvent>(Channel.CreateUnbounded<KernelProcessEvent>());

        await observableChannel.WriteAsync(s_testEvent1);
        await observableChannel.WriteAsync(s_testEvent2);
        await observableChannel.WriteAsync(s_testEvent3);

        // Act
        var snapshot = observableChannel.GetChannelSnapshot();
        observableChannel.TryPeak(out var peakChannelItem);

        // Assert
        Assert.Equal(3, snapshot.Count);
        Assert.Contains(snapshot, e => e.Id == s_testEvent1.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent2.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent3.Id);
        Assert.NotNull(peakChannelItem);
        Assert.Equal(s_testEvent1.Id, peakChannelItem?.Id);
    }

    [Fact]
    public async Task VerifyAfterAddingWithTryWriteAsyncItemsGetSnapshotAsync()
    {
        // Arrange
        var observableChannel = new ObservableChannel<KernelProcessEvent>(Channel.CreateUnbounded<KernelProcessEvent>());

        observableChannel.TryWrite(s_testEvent1);
        observableChannel.TryWrite(s_testEvent2);
        observableChannel.TryWrite(s_testEvent3);

        // Act
        var snapshot = observableChannel.GetChannelSnapshot();
        observableChannel.TryPeak(out var peakChannelItem);

        // Assert
        Assert.Equal(3, snapshot.Count);
        Assert.Contains(snapshot, e => e.Id == s_testEvent1.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent2.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent3.Id);
        Assert.NotNull(peakChannelItem);
        Assert.Equal(s_testEvent1.Id, peakChannelItem?.Id);
    }

    [Fact]
    public async Task VerifyReturnsEmptyArrayWhenNoItemsAddedAsync()
    {
        // Arrange
        var observableChannel = new ObservableChannel<KernelProcessEvent>(Channel.CreateUnbounded<KernelProcessEvent>());

        // Act
        var snapshot = observableChannel.GetChannelSnapshot();
        observableChannel.TryPeak(out var peakChannelItem);

        // Assert
        Assert.Empty(snapshot);
        Assert.Null(peakChannelItem);
    }

    [Fact]
    public async Task VerifyChannelRehydratedProperlyFromInitialStateAsync()
    {
        // Arrange
        var initialState = new KernelProcessEvent[]
        {
            s_testEvent1,
            s_testEvent2,
            s_testEvent3,
        };
        var observableChannel = new ObservableChannel<KernelProcessEvent>(Channel.CreateUnbounded<KernelProcessEvent>(), initialState: initialState);

        // Act
        var snapshot = observableChannel.GetChannelSnapshot();
        observableChannel.TryPeak(out var peakChannelItem);

        // Assert
        Assert.Equal(3, snapshot.Count);
        Assert.Contains(snapshot, e => e.Id == s_testEvent1.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent2.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent3.Id);
        Assert.NotNull(peakChannelItem);
        Assert.Equal(s_testEvent1.Id, peakChannelItem?.Id);
    }

    [Fact]
    public async Task VerifyChannelRehydratedProperlyFromInitialStateAndReadingItemAfterAsync()
    {
        // Arrange
        var initialState = new KernelProcessEvent[]
        {
            s_testEvent1,
            s_testEvent2,
            s_testEvent3,
        };
        var observableChannel = new ObservableChannel<KernelProcessEvent>(Channel.CreateUnbounded<KernelProcessEvent>(), initialState: initialState);

        // Act
        observableChannel.TryRead(out _); // Read the first item
        var snapshot = observableChannel.GetChannelSnapshot();
        observableChannel.TryPeak(out var peakChannelItem);

        // Assert
        Assert.Equal(2, snapshot.Count);
        Assert.DoesNotContain(snapshot, e => e.Id == s_testEvent1.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent2.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent3.Id);
        Assert.NotNull(peakChannelItem);
        Assert.Equal(s_testEvent2.Id, peakChannelItem?.Id);
    }

    [Fact]
    public async Task VerifyChannelRehydratedProperlyFromInitialStateAndAddingItemAfterAsync()
    {
        // Arrange
        var initialState = new KernelProcessEvent[]
        {
            s_testEvent1,
            s_testEvent2,
        };
        var observableChannel = new ObservableChannel<KernelProcessEvent>(Channel.CreateUnbounded<KernelProcessEvent>(), initialState: initialState);

        // Act
        observableChannel.TryWrite(s_testEvent3); // Read the first item
        var snapshot = observableChannel.GetChannelSnapshot();
        observableChannel.TryPeak(out var peakChannelItem);

        // Assert
        Assert.Equal(3, snapshot.Count);
        Assert.Contains(snapshot, e => e.Id == s_testEvent1.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent2.Id);
        Assert.Contains(snapshot, e => e.Id == s_testEvent3.Id);
        Assert.NotNull(peakChannelItem);
        Assert.Equal(s_testEvent1.Id, peakChannelItem?.Id);
    }
}
