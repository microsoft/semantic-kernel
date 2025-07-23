// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Internal;
using Xunit;

namespace SemanticKernel.Process.Utilities.UnitTests;

/// <summary>
/// Tests for <see cref="ObservableChannel{T}"/>.
/// </summary>
public class ObservableChannelTests
{
    private static readonly KernelProcessEvent s_testEvent1 = new() { Data = "someData1", Id = "myId1", Visibility = KernelProcessEventVisibility.Public };
    private static readonly KernelProcessEvent s_testEvent2 = new() { Data = "someData2", Id = "myId2", Visibility = KernelProcessEventVisibility.Public };
    private static readonly KernelProcessEvent s_testEvent3 = new() { Data = "someData3", Id = "myId3", Visibility = KernelProcessEventVisibility.Public };

    /// <summary>
    /// Tests that items added to the channel can be read and peeked correctly.
    /// </summary>
    /// <returns></returns>
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

    /// <summary>
    /// Tests that items added to the channel can be read and peeked correctly using TryWriteAsync.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public void VerifyAfterAddingWithTryWriteAsyncItemsGetSnapshot()
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

    /// <summary>
    /// Tests that the channel returns an empty array when no items have been added.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public void VerifyReturnsEmptyArrayWhenNoItemsAdded()
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

    /// <summary>
    /// Tests that the channel can be rehydrated from an initial state and returns the correct snapshot.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public void VerifyChannelRehydratedProperlyFromInitialState()
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

    /// <summary>
    /// Tests that the channel can be rehydrated from an initial state and reading an item after that returns the correct snapshot.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public void VerifyChannelRehydratedProperlyFromInitialStateAndReadingItemAfter()
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
    public void VerifyChannelRehydratedProperlyFromInitialStateAndAddingItemAfter()
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
