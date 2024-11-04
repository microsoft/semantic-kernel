//// Copyright (c) Microsoft. All rights reserved.
//using System;
//using Microsoft.SemanticKernel;
//using Microsoft.SemanticKernel.Process.Runtime;
//using Xunit;

//namespace SemanticKernel.Process.Utilities.UnitTests;

///// <summary>
///// Unit tests for the <see cref="ProcessEvent"/> class.
///// </summary>
//public class EventFactoryTests
//{
//    /// <summary>
//    /// Verify factory creation of <see cref="KernelProcessEvent"/> without data.
//    /// </summary>
//    [Fact]
//    public void CreateKernelProcessEventWithoutDataTest()
//    {
//        // Arrange & Act
//        KernelProcessEvent processEvent = EventFactory.CreateKernelProcessEvent("test", null);

//        // Assert
//        Assert.NotNull(processEvent);
//        Assert.IsType<KernelProcessEvent>(processEvent);
//        Assert.False(processEvent.GetType().IsGenericType);
//        Assert.Null(processEvent.GetData());
//    }

//    /// <summary>
//    /// Verify factory creation of <see cref="KernelProcessEvent"/> with data.
//    /// </summary>
//    [Fact]
//    public void CreateKernelProcessEventWithDataTest()
//    {
//        // Arrange
//        Guid data = Guid.NewGuid();

//        // Act
//        KernelProcessEvent processEvent = EventFactory.CreateKernelProcessEvent("test", data);

//        // Assert
//        Assert.NotNull(processEvent);
//        Assert.IsType<KernelProcessEvent<Guid>>(processEvent);
//        Assert.Equal(data, processEvent.GetData());
//    }

//    /// <summary>
//    /// Verify factory creation of <see cref="ProcessEvent"/> without data.
//    /// </summary>
//    [Fact]
//    public void CreateProcessEventWithoutDataTest()
//    {
//        // Arrange & Act
//        ProcessEvent processEvent = EventFactory.CreateProcessEvent("test", "test", null);

//        // Assert
//        Assert.NotNull(processEvent);
//        Assert.IsType<ProcessEvent>(processEvent);
//        Assert.False(processEvent.GetType().IsGenericType);
//        Assert.Null(processEvent.GetData());
//    }

//    /// <summary>
//    /// Verify factory creation of <see cref="ProcessEvent"/> with data.
//    /// </summary>
//    [Fact]
//    public void CreateProcessEventWithDataTest()
//    {
//        // Arrange
//        Guid data = Guid.NewGuid();

//        // Arrange
//        ProcessEvent processEvent = EventFactory.CreateProcessEvent("test", "test", data);

//        // Assert
//        Assert.NotNull(processEvent);
//        Assert.IsType<ProcessEvent<Guid>>(processEvent);
//        Assert.Equal(data, processEvent.GetData());
//    }
//}
