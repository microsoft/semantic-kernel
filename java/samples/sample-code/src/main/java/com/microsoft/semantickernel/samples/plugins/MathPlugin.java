// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.plugins;

import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;

public class MathPlugin {

    @DefineKernelFunction(name = "sqrt", description = "Take the square root of a number")
    public static double sqrt(
        @KernelFunctionParameter(name = "number1", description = "The number to take a square root of", type = double.class) double number1) {
        return Math.sqrt(number1);
    }

    @DefineKernelFunction(name = "add", description = "Add two numbers")
    public static double add(
        @KernelFunctionParameter(name = "number1", description = "The first number to add", type = double.class) double number1,
        @KernelFunctionParameter(name = "number2", description = "The second number to add", type = double.class) double number2) {
        return number1 + number2;
    }

    @DefineKernelFunction(name = "subtract", description = "Subtract two numbers")
    public static double subtract(
        @KernelFunctionParameter(name = "number1", description = "The first number to subtract from", type = double.class) double number1,
        @KernelFunctionParameter(name = "number2", description = "The second number to subtract away", type = double.class) double number2) {
        return number1 - number2;
    }

    @DefineKernelFunction(name = "multiply", description = "Multiply two numbers. When increasing by a percentage, don't forget to add 1 to the percentage.")
    public static double multiply(
        @KernelFunctionParameter(name = "number1", description = "The first number to multiply", type = double.class) double number1,
        @KernelFunctionParameter(name = "number2", description = "The second number to multiply", type = double.class) double number2) {
        return number1 * number2;
    }

    @DefineKernelFunction(name = "divide", description = "Divide two numbers")
    public static double divide(
        @KernelFunctionParameter(name = "number1", description = "The first number to divide from", type = double.class) double number1,
        @KernelFunctionParameter(name = "number2", description = "The second number to divide by", type = double.class) double number2) {
        return number1 / number2;
    }

    @DefineKernelFunction(name = "power", description = "Raise a number to a power")
    public static double power(
        @KernelFunctionParameter(name = "number1", description = "The number to raise", type = double.class) double number1,
        @KernelFunctionParameter(name = "number2", description = "The power to raise the number to", type = double.class) double number2) {
        return Math.pow(number1, number2);
    }

    @DefineKernelFunction(name = "log", description = "Take the log of a number")
    public static double log(
        @KernelFunctionParameter(name = "number1", description = "The number to take the log of", type = double.class) double number1,
        @KernelFunctionParameter(name = "number2", description = "The base of the log", type = double.class) double number2) {
        return Math.log(number1) / Math.log(number2);
    }

    @DefineKernelFunction(name = "round", description = "Round a number to the target number of decimal places")
    public static double round(
        @KernelFunctionParameter(name = "number1", description = "The number to round", type = double.class) double number1,
        @KernelFunctionParameter(name = "number2", description = "The number of decimal places to round to", type = double.class) int number2) {
        return Math.round(number1 * Math.pow(10, number2)) / Math.pow(10, number2);
    }

    @DefineKernelFunction(name = "abs", description = "Take the absolute value of a number")
    public static double abs(
        @KernelFunctionParameter(name = "number1", description = "The number to take the absolute value of", type = double.class) double number1) {
        return Math.abs(number1);
    }

    @DefineKernelFunction(name = "floor", description = "Take the floor of a number")
    public static double floor(
        @KernelFunctionParameter(name = "number1", description = "The number to take the floor of", type = double.class) double number1) {
        return Math.floor(number1);
    }

    @DefineKernelFunction(name = "ceiling", description = "Take the ceiling of a number")
    public static double ceiling(
        @KernelFunctionParameter(name = "number1", description = "The number to take the ceiling of", type = double.class) double number1) {
        return Math.ceil(number1);
    }

    @DefineKernelFunction(name = "sin", description = "Take the sine of a number")
    public static double sin(
        @KernelFunctionParameter(name = "number1", description = "The number to take the sine of", type = double.class) double number1) {
        return Math.sin(number1);
    }

    @DefineKernelFunction(name = "cos", description = "Take the cosine of a number")
    public static double cos(
        @KernelFunctionParameter(name = "number1", description = "The number to take the cosine of", type = double.class) double number1) {
        return Math.cos(number1);
    }

    @DefineKernelFunction(name = "tan", description = "Take the tangent of a number")
    public static double tan(
        @KernelFunctionParameter(name = "number1", description = "The number to take the tangent of", type = double.class) double number1) {
        return Math.tan(number1);
    }

    @DefineKernelFunction(name = "asin", description = "Take the arcsine of a number")
    public static double asin(
        @KernelFunctionParameter(name = "number1", description = "The number to take the arcsine of", type = double.class) double number1) {
        return Math.asin(number1);
    }

    @DefineKernelFunction(name = "acos", description = "Take the arccosine of a number")
    public static double acos(
        @KernelFunctionParameter(name = "number1", description = "The number to take the arccosine of", type = double.class) double number1) {
        return Math.acos(number1);
    }

    @DefineKernelFunction(name = "atan", description = "Take the arctangent of a number")
    public static double atan(
        @KernelFunctionParameter(name = "number1", description = "The number to take the arctangent of", type = double.class) double number1) {
        return Math.atan(number1);
    }
}
