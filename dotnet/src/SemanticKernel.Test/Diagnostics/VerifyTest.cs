// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;
using Xunit;

namespace SemanticKernelTests.Diagnostics;

public class VerifyTests
{
    #region Verify.GreaterThan
    [Fact]
    public void GreaterThanThrowsWhenValueIsLessThanOrEqualToTarget()
    {
        var ex = Assert.Throws<ValidationException>(() => Verify.GreaterThan<int>(-1, 0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.GreaterThan<double>(0.0, 0.0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.GreaterThan<TimeSpan>(TimeSpan.MinValue, TimeSpan.MaxValue));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);
    }

    [Fact]
    public void GreaterThanPassesWhenValueIsGreaterThanTarget()
    {
        Verify.GreaterThan<int>(1, 0);
        Verify.GreaterThan<double>(1.0, 0.0);
        Verify.GreaterThan<TimeSpan>(TimeSpan.MaxValue, TimeSpan.MinValue);
    }
    #endregion

    #region Verify.GreaterThanOrEqualTo
    [Fact]
    public void GreaterThanOrEqualToThrowsWhenValueIsLessThanTarget()
    {
        var ex = Assert.Throws<ValidationException>(() => Verify.GreaterThanOrEqualTo<int>(-1, 0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.GreaterThan<double>(-0.1, 0.0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.GreaterThan<TimeSpan>(TimeSpan.MinValue, TimeSpan.MaxValue));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);
    }

    [Fact]
    public void GreaterThanOrEqualToPassesWhenValueIsGreaterThanOrEqualToTarget()
    {
        Verify.GreaterThanOrEqualTo<int>(1, 0);
        Verify.GreaterThanOrEqualTo<double>(0.0, 0.0);
        Verify.GreaterThanOrEqualTo<TimeSpan>(TimeSpan.MaxValue, TimeSpan.MinValue);
    }
    #endregion

    #region Verify.LessThan
    [Fact]
    public void LessThanThrowsWhenValueIsGreaterThanOrEqualToTarget()
    {
        var ex = Assert.Throws<ValidationException>(() => Verify.LessThan<int>(1, 0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.LessThan<double>(0.0, 0.0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.LessThan<TimeSpan>(TimeSpan.MaxValue, TimeSpan.MinValue));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);
    }

    [Fact]
    public void LessThanPassesWhenValueIsLessThanTarget()
    {
        Verify.LessThan<int>(-1, 0);
        Verify.LessThan<double>(-0.1, 0.0);
        Verify.LessThan<TimeSpan>(TimeSpan.MinValue, TimeSpan.MaxValue);
    }
    #endregion

    #region Verify.LessThanOrEqualTo
    [Fact]
    public void LessThanOrEqualToThrowsWhenValueIsGreaterThanTarget()
    {
        var ex = Assert.Throws<ValidationException>(() => Verify.LessThanOrEqualTo<int>(1, 0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.LessThanOrEqualTo<double>(0.1, 0.0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.LessThanOrEqualTo<TimeSpan>(TimeSpan.MaxValue, TimeSpan.MinValue));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);
    }

    [Fact]
    public void LessThanOrEqualToPassesWhenValueIsLessThanOrEqualToTarget()
    {
        Verify.LessThanOrEqualTo<int>(-1, 0);
        Verify.LessThanOrEqualTo<double>(0.0, 0.0);
        Verify.LessThanOrEqualTo<TimeSpan>(TimeSpan.MinValue, TimeSpan.MaxValue);
    }
    #endregion

    #region Verify.WithinRange
    [Fact]
    public void WithinRangeThrowsWhenValueIsNotWithinRange()
    {
        var ex = Assert.Throws<ValidationException>(() => Verify.WithinRange<int>(1, 0, 0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.WithinRange<double>(0.0, 0.0, 0.1));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.WithinRange<TimeSpan>(TimeSpan.MaxValue, TimeSpan.MinValue, TimeSpan.FromDays(1)));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);
    }

    [Fact]
    public void WithinRangePassesWhenValueIsWithinRange()
    {
        Verify.WithinRange<int>(-1, -2, 0);
        Verify.WithinRange<double>(0.0, -0.1, 0.1);
        Verify.WithinRange<TimeSpan>(TimeSpan.FromDays(1), TimeSpan.MinValue, TimeSpan.MaxValue);
    }
    #endregion

    #region Verify.WithinRangeInclusive
    [Fact]
    public void WithinRangeInclusiveThrowsWhenValueIsNotWithinRange()
    {
        var ex = Assert.Throws<ValidationException>(() => Verify.WithinRangeInclusive<int>(1, 0, 0));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.WithinRangeInclusive<double>(-0.1, 0.0, 0.1));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);

        ex = Assert.Throws<ValidationException>(() => Verify.WithinRangeInclusive<TimeSpan>(TimeSpan.MaxValue, TimeSpan.MinValue, TimeSpan.FromDays(1)));
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, ex.ErrorCode);
    }

    [Fact]
    public void WithinRangeInclusivePassesWhenValueIsWithinRange()
    {
        Verify.WithinRangeInclusive<int>(-1, -1, 0);
        Verify.WithinRangeInclusive<double>(0.1, -0.1, 0.1);
        Verify.WithinRangeInclusive<TimeSpan>(TimeSpan.FromDays(1), TimeSpan.MinValue, TimeSpan.MaxValue);
    }
    #endregion
}
