// Copyright (c) Microsoft. All rights reserved.
package plugins.mathplugin;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.Map;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.skilldefinition.annotations.SKSample;
import com.microsoft.semantickernel.planner.handlebarsplanner.HandlebarsPlan;
import com.microsoft.semantickernel.planner.handlebarsplanner.HandlebarsPlanner;
import com.microsoft.semantickernel.planner.handlebarsplanner.HandlebarsPlanner.HandlebarsPlannerConfiguration;

import reactor.core.publisher.Mono;

public class Math
{

    public Math() {
    }

    @DefineSKFunction(
        name = "Math.PerformMath",
        description = "Uses functions from the Math plugin to solve math problems.",
        returnDescription = "The answer to the math problem.",
        samples = {
            @SKSample(
                inputs = "{\"math_problem\",\"If I started with $120 in the stock market, how much would I have after 10 years if the growth rate was 5%?\"}",
                output = "After 10 years, starting with $120, and with a growth rate of 5%, you would have $195.47 in the stock market."
            )
        }
    )
    public static Mono<String> performMath(
        Kernel kernel,
        @SKFunctionParameters(name="math_problem", description="A description of a math problem; use the GenerateMathProblem function to create one.")
        String math_problem
    ) 
    {
        int maxTries = 1;
        HandlebarsPlan lastPlan = null;
        Exception lastError = null;

        // Create the planner
        var planner = new HandlebarsPlanner(
            kernel, 
            new HandlebarsPlannerConfiguration()
                .setIncludedPlugins(List.of("Math"))
                .setIncludedFunctions(List.of("Math.PerformMath", "Math.GenerateMathProblem"))
                // TODO: setLastPlan and setLastError are problematic 
                // (null to begin with, how to set them later, does planner need to be recreated each time?)
                //.setLastPlan(lastPlan) // Pass in the last plan in case we want to try again
                //.setLastError(lastError.getMessage()) // Pass in the last error to avoid trying the same thing again
        );

        Mono<String> plan = 
            planner.createPlanAsync("Solve the following math problem.\n\n" + math_problem)
                .flatMap(handlebarsPlan -> handlebarsPlan.invokeAsync(kernel, Map.of()))
                .retry(maxTries)
                .flatMap(result -> result.<String>getValueAsync());

        return plan;
        
}
    

    @DefineSKFunction(
        name = "Math.Add",
        description = "Adds two numbers.",
        returnDescription = "The summation of the numbers.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":1, \"number2\":2}",
                output = "3"
            )
        }
    )
    public static double add(
        @SKFunctionParameters(description="The first number to add", name="number1") double number1,
        @SKFunctionParameters(description="The second number to add", name="number2") double number2
    )
    {
        return number1 + number2;
    }


    @DefineSKFunction(
        name = "Math.Subtract",
        description = "Subtracts two numbers.",
        returnDescription = "The difference between the minuend and subtrahend.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":5, \"number2\":2}",
                output = "3"
            )
        }
    )
    public static double subtract(
        @SKFunctionParameters(description="The minuend", name="number1") double number1,
        @SKFunctionParameters(description="The subtrahend", name="number2") double number2
    )
    {
        return number1 - number2;
    }

    @DefineSKFunction(
        name = "Math.Multiply",
        description = "Multiplies two numbers.",
        returnDescription = "The product of the numbers.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":5, \"number2\":2}",
                output = "10"
            )
        }
    )
    public static double multiply(
        @SKFunctionParameters(description="The first number to multiply", name="number1") double number1,
        @SKFunctionParameters(description="The second number to multiply", name="number2") double number2
    )
    {
        return number1 * number2;
    }

    @DefineSKFunction(
        name = "Math.Divide",
        description = "Divides two numbers.",
        returnDescription = "The quotient of the dividend and divisor.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":10, \"number2\":2}",
                output = "5"
            )
        }
    )
    public static double divide(
        @SKFunctionParameters(description="The dividend", name="number1") double number1,
        @SKFunctionParameters(description="The divisor", name="number2") double number2
    )
    {
        return number1 / number2;
    }

    @DefineSKFunction(
        name = "Math.Modulo",
        description = "Gets the remainder of two numbers.",
        returnDescription = "The remainder of the dividend and divisor.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":10, \"number2\":3}",
                output = "1"
            )
        }
    )
    public static double modulo(
        @SKFunctionParameters(description="The dividend", name="number1") double number1,
        @SKFunctionParameters(description="The divisor", name="number2") double number2
    )
    {
        return number1 % number2;
    }


    @DefineSKFunction(
        name = "Math.Abs",
        description = "Gets the absolute value of a number.",
        returnDescription = "The absolute value of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":-10}",
                output = "10"
            )
        }
    )
    public static double abs(
        @SKFunctionParameters(description="The number", name="number1") double number1
    )
    {
        return java.lang.Math.abs(number1);
    }

    @DefineSKFunction(
        name = "Math.Ceil",
        description = "Gets the ceiling of a single number.",
        returnDescription = "The ceiling of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":5.1}",
                output = "6"
            )
        }
    )
    public static double ceil(
        @SKFunctionParameters(description="The number", name="number1") double number1
    )
    {
        return java.lang.Math.ceil(number1);
    }

    
    @DefineSKFunction(
        name = "Math.Floor",
        description = "Gets the floor of a single number.",
        returnDescription = "The floor of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":5.9}",
                output = "5"
            )
        }
    )
    public static double floor(
        @SKFunctionParameters(description="The number", name="number1") double number1
    )
    {
        return java.lang.Math.floor(number1);
    }

    @DefineSKFunction(
        name = "Math.Max",
        description = "Gets the maximum of two numbers.",
        returnDescription = "The maximum of the two numbers.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":5, \"number2\":10}",
                output = "10"
            )
        }
    )
    public static double max(
        @SKFunctionParameters(description="The first number", name="number1") double number1,
        @SKFunctionParameters(description="The second number", name="number2") double number2
    )
    {
        return java.lang.Math.max(number1, number2);
    }

    @DefineSKFunction(
        name = "Math.Min",
        description = "Gets the minimum of two numbers.",
        returnDescription = "The minimum of the two numbers.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":5, \"number2\":10}",
                output = "5"
            )
        }
    )
    public static double min(
        @SKFunctionParameters(description="The first number", name="number1") double number1,
        @SKFunctionParameters(description="The second number", name="number2") double number2
    )
    {
        return java.lang.Math.min(number1, number2);
    }

    @DefineSKFunction(
        name = "Math.Sign",
        description = "Gets the sign of a number.",
        returnDescription = "The sign of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":-10}",
                output = "-1"
            )
        }
    )
    public static double sign(
        @SKFunctionParameters(description="The number", name="number1") double number1
    )
    {
        return Double.compare(number1,0d) >= 0 ? 1d : -1d;
    }

    @DefineSKFunction(
        name = "Math.Sqrt",
        description = "Gets the square root of a number.",
        returnDescription = "The square root of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":25}",
                output = "5"
            )
        }
    )
    public static double sqrt(
        @SKFunctionParameters(description="The number", name="number1") double number1
    )
    {
        return java.lang.Math.sqrt(number1);
    }

    @DefineSKFunction(
        name = "Math.Sin",
        description = "Gets the sine of a number.",
        returnDescription = "The sine of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":0}",
                output = "0"
            )
        }
    )
    public static double sin(
        @SKFunctionParameters(description="The number", name="number1") double number1
    )
    {
        return java.lang.Math.sin(number1);
    }

    @DefineSKFunction(
        name = "Math.Cos",
        description = "Gets the cosine of a number.",
        returnDescription = "The cosine of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":0}",
                output = "1"
            )
        }
    )
    public static double cos(
        @SKFunctionParameters(description="The number", name="number1") double number1
    )
    {
        return java.lang.Math.cos(number1);
    }

    @DefineSKFunction(
        name = "Math.Tan",
        description = "Gets the tangent of a number.",
        returnDescription = "The tangent of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":0}",
                output = "0"
            )
        }
    )
    public static double tan(
        @SKFunctionParameters(description="The number", name="number1") double number1
    )
    {
        return java.lang.Math.tan(number1);
    }

    @DefineSKFunction(
        name = "Math.Pow",
        description = "Raises a number to a power.",
        returnDescription = "The number raised to the power.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":5, \"number2\":2}",
                output = "25"
            )
        }
    )
    public static double pow(
        @SKFunctionParameters(description="The number", name="number1") double number1,
        @SKFunctionParameters(description="The power", name="number2") double number2
    )
    {
        return java.lang.Math.pow(number2, number2);
    }

    @DefineSKFunction(
        name = "Math.Log",
        description = "Gets the natural logarithm of a number.",
        returnDescription = "The natural logarithm of the number.",
        samples = {
            @SKSample(
                inputs = "{\"number1\":10, \"number2\":10}",
                output = "2.302585092994046"
            )
        }
    )
    public static double Log(
        @SKFunctionParameters(description="The number", name="number1") double number1,
        @SKFunctionParameters(description="The base of the logarithm", name="number2", defaultValue="10") double number2
    )
    {
        if (Double.isNaN(number2)) {
            return java.lang.Math.log(number1);
        }
        if (Double.compare(number2, 1d) > 0) {
            return divide(java.lang.Math.log(number1), java.lang.Math.log(number2));
        }
        throw new IllegalArgumentException("The base of the logarithm must be greater than 1.");
    }

    @DefineSKFunction(
        name = "Math.Round",
        description = "Gets a rounded number.",
        returnDescription = "The rounded number.",
        samples = {
            @SKSample(
                inputs = "{\"number\":1.23456, \"digits\":2}",
                output = "1.23"
            )
        }
    )
    public static double round(
        @SKFunctionParameters(description="The number", name="number1") double number1,
        @SKFunctionParameters(description="The number of digits to round to", name="number2", defaultValue="0") int number2
    )
    {
        if (number2 < 0) throw new IllegalArgumentException("The number of digits to round to must be greater than or equal to 0.");

        BigDecimal bd = new BigDecimal(Double.toString(number1));
        bd = bd.setScale(number2, RoundingMode.HALF_UP);
        return bd.doubleValue();
    }
}