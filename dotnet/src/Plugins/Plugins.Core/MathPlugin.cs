// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// MathPlugin provides a set of functions to make Math calculations.
/// </summary>
public sealed class MathPlugin
{
    [KernelFunction]
    [Description("Adds two numbers. This takes only 2 numbers.")]
    [return: Description("The summation of the numbers.")]
    public static double Add(
       [Description("The first number to add")] double number1,
       [Description("The second number to add")] double number2)
    {
        return number1 + number2;
    }

    [KernelFunction]
    [Description("Subtracts two numbers. This takes only 2 numbers.")]
    [return: Description("The difference between the minuend and subtrahend.")]
    public static double Subtract(
        [Description("The minuend")] double number1,
        [Description("The subtrahend")] double number2)
    {
        return number1 - number2;
    }

    [KernelFunction]
    [Description("Multiplies two numbers. This takes only 2 numbers.")]
    [return: Description("The product of the numbers.")]
    public static double Multiply(
        [Description("The first number to multiply")] double number1,
        [Description("The second number to multiply")] double number2)
    {
        return number1 * number2;
    }

    [KernelFunction]
    [Description("Divides two numbers. This takes only 2 numbers.")]
    [return: Description("The quotient of the dividend and divisor.")]
    public static double Divide(
        [Description("The dividend")] double number1,
        [Description("The divisor")] double number2)
    {
        return number1 / number2;
    }

    [KernelFunction]
    [Description("Gets the remainder of two numbers. This takes only 2 numbers.")]
    [return: Description("The remainder of the dividend and divisor.")]
    public static double Modulo(
        [Description("The dividend")] double number1,
        [Description("The divisor")] double number2)
    {
        return number1 % number2;
    }

    [KernelFunction]
    [Description("Gets the absolute value of a number.")]
    [return: Description("The absolute value of the number.")]
    public static double Abs(
        [Description("The number")] double number1)
    {
        return System.Math.Abs(number1);
    }

    [KernelFunction]
    [Description("Gets the ceiling of a single number.")]
    [return: Description("The ceiling of the number.")]
    public static double Ceil(
        [Description("The number")] double number1)
    {
        return System.Math.Ceiling(number1);
    }

    [KernelFunction]
    [Description("Gets the floor of a single number.")]
    [return: Description("The floor of the number.")]
    public static double Floor(
        [Description("The number")] double number1)
    {
        return System.Math.Floor(number1);
    }

    [KernelFunction]
    [Description("Gets the maximum of two numbers. This takes only 2 numbers.")]
    [return: Description("The maximum of the two numbers.")]
    public static double Max(
        [Description("The first number")] double number1,
        [Description("The second number")] double number2)
    {
        return System.Math.Max(number1, number2);
    }

    [KernelFunction]
    [Description("Gets the minimum of two numbers. This takes only 2 numbers.")]
    [return: Description("The minimum of the two numbers.")]
    public static double Min(
        [Description("The first number")] double number1,
        [Description("The second number")] double number2)
    {
        return System.Math.Min(number1, number2);
    }

    [KernelFunction]
    [Description("Gets the sign of a number.")]
    [return: Description("The sign of the number.")]
    public static double Sign(
        [Description("The number")] double number1)
    {
        return System.Math.Sign(number1);
    }

    [KernelFunction]
    [Description("Gets the square root of a number.")]
    [return: Description("The square root of the number.")]
    public static double Sqrt(
        [Description("The number")] double number1)
    {
        return System.Math.Sqrt(number1);
    }

    [KernelFunction]
    [Description("Gets the sine of a number.")]
    [return: Description("The sine of the number.")]
    public static double Sin(
        [Description("The number")] double number1)
    {
        return System.Math.Sin(number1);
    }

    [KernelFunction]
    [Description("Gets the cosine of a number.")]
    [return: Description("The cosine of the number.")]
    public static double Cos(
        [Description("The number")] double number1)
    {
        return System.Math.Cos(number1);
    }

    [KernelFunction]
    [Description("Gets the tangent of a number.")]
    [return: Description("The tangent of the number.")]
    public static double Tan(
        [Description("The number")] double number1)
    {
        return System.Math.Tan(number1);
    }

    [KernelFunction]
    [Description("Raises a number to a power.")]
    [return: Description("The number raised to the power.")]
    public static double Pow(
        [Description("The number")] double number1,
        [Description("The power")] double number2)
    {
        return System.Math.Pow(number1, number2);
    }

    [KernelFunction]
    [Description("Gets the natural logarithm of a number.")]
    [return: Description("The natural logarithm of the number.")]
    public static double Log(
        [Description("The number")] double number1,
        [Description("The base of the logarithm")] double number2 = 10)
    {
        return System.Math.Log(number1, number2);
    }

    [KernelFunction]
    [Description("Gets a rounded number.")]
    [return: Description("The rounded number.")]
    public static double Round(
        [Description("The number")] double number1,
        [Description("The number of digits to round to")] int number2 = 0)
    {
        return System.Math.Round(number1, number2);
    }
}
