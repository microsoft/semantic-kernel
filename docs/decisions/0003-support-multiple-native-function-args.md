---
# These are optional elements. Feel free to remove any of them.
status: accepted
date: 2023-06-16
deciders: shawncal,dluc
consulted: 
informed: 
---
# Add support for multiple native function arguments of many types

## Context and Problem Statement

Move native functions closer to a normal C# experience.

## Decision Drivers

- Native skills can now have any number of parameters. The parameters are populated from context variables of the same name.  If no context variable exists for that name, it'll be populated with a default value if one was supplied via either an attribute or a default parameter value, or if there is none, the function will fail to be invoked. The first parameter may also be populated from "input" if it fails to get input by its name or default value.
- Descriptions are now specified with the .NET DescriptionAttribute, and DefaultValue with the DefaultValueAttribute.  The C# compiler is aware of the DefaultValueAttribute and ensures the type of the value provided matches that of the type of the parameter.  Default values can now also be specified using optional parameter values.
- SKFunction is now purely a marker attribute, other than for sensitivity. It's sole purpose is to subset which public members are imported as native functions when a skill is imported. It was already the case that the attribute wasn't needed when importing a function directly from a delegate; that requirement has also been lifted when importing from a MethodInfo.
- SKFunctionContextParameterAttribute has been obsoleted and will be removed subsequently.  DescriptionAttribute, DefaultValueAttribute, and SKName attribute are used instead.  In rare situations where the method needs access to a variable that's not defined in its signature, it can use the SKParameter attribute on the method, which does have Description and DefaultValue optional properties.
- SKFunctionInputAttribute has been obsoleted and will be removed subsequently.  DescriptionAttribute, DefaultValueAttribute, and SKName attribute are used instead (the latter with "Input" as the name). However, the need to use SKName should be exceedingly rare.
- InvokeAsync will now catch exceptions and store the exception into the context.  This means native skills should handle all failures by throwing exceptions rather than by directly interacting with the context.
- Updated name selection heuristic to strip off an "Async" suffix for async methods.  There are now very few reasons to use [SKName] on a method.
- Added support for ValueTasks as return types, just for completeness so that developers don't need to think about it. It just works.
- Added ability to accept an ILogger or CancellationToken into a method; they're populated from the SKContext.  With that, there are very few reasons left to pass an SKContext into a native function.
- Added support for non-string arguments. All C# primitive types and many core .NET types are supported, with their corresponding TypeConverters used to parse the string context variable into the appropriate type. Custom types attributed with TypeConverterAttribute may also be used, and the associated TypeConverter will be used as is appropriate.  It's the same mechanism used by UI frameworks like WinForms as well as ASP.NET MVC.
- Similarly, added support for non-string return types.

## Decision Outcome

[PR 1195](https://github.com/microsoft/semantic-kernel/pull/1195)

## More Information

**Example**

_Before_:

```C#
[SKFunction("Adds value to a value")]
[SKFunctionName("Add")]
[SKFunctionInput(Description = "The value to add")]
[SKFunctionContextParameter(Name = "Amount", Description = "Amount to add")]
public Task<string> AddAsync(string initialValueText, SKContext context)
{
    if (!int.TryParse(initialValueText, NumberStyles.Any, CultureInfo.InvariantCulture, out var initialValue))
    {
        return Task.FromException<string>(new ArgumentOutOfRangeException(
            nameof(initialValueText), initialValueText, "Initial value provided is not in numeric format"));
    }

    string contextAmount = context["Amount"];
    if (!int.TryParse(contextAmount, NumberStyles.Any, CultureInfo.InvariantCulture, out var amount))
    {
        return Task.FromException<string>(new ArgumentOutOfRangeException(
            nameof(context), contextAmount, "Context amount provided is not in numeric format"));
    }

    var result = initialValue + amount;
    return Task.FromResult(result.ToString(CultureInfo.InvariantCulture));
}
```

_After_:

```C#
[SKFunction, Description("Adds an amount to a value")]
public int Add(
    [Description("The value to add")] int value,
    [Description("Amount to add")] int amount) =>
    value + amount;
```

**Example**

_Before_:

```C#
[SKFunction("Wait a given amount of seconds")]
[SKFunctionName("Seconds")]
[SKFunctionInput(DefaultValue = "0", Description = "The number of seconds to wait")]
public async Task SecondsAsync(string secondsText)
{
    if (!decimal.TryParse(secondsText, NumberStyles.Any, CultureInfo.InvariantCulture, out var seconds))
    {
        throw new ArgumentException("Seconds provided is not in numeric format", nameof(secondsText));
    }

    var milliseconds = seconds * 1000;
    milliseconds = (milliseconds > 0) ? milliseconds : 0;

    await this._waitProvider.DelayAsync((int)milliseconds).ConfigureAwait(false);
}
```

_After_:

```C#
[SKFunction, Description("Wait a given amount of seconds")]
public async Task SecondsAsync([Description("The number of seconds to wait")] decimal seconds)
{
    var milliseconds = seconds * 1000;
    milliseconds = (milliseconds > 0) ? milliseconds : 0;

    await this._waitProvider.DelayAsync((int)milliseconds).ConfigureAwait(false);
}
```

**Example**

_Before_:

```C#
[SKFunction("Add an event to my calendar.")]
[SKFunctionInput(Description = "Event subject")]
[SKFunctionContextParameter(Name = Parameters.Start, Description = "Event start date/time as DateTimeOffset")]
[SKFunctionContextParameter(Name = Parameters.End, Description = "Event end date/time as DateTimeOffset")]
[SKFunctionContextParameter(Name = Parameters.Location, Description = "Event location (optional)")]
[SKFunctionContextParameter(Name = Parameters.Content, Description = "Event content/body (optional)")]
[SKFunctionContextParameter(Name = Parameters.Attendees, Description = "Event attendees, separated by ',' or ';'.")]
public async Task AddEventAsync(string subject, SKContext context)
{
    ContextVariables variables = context.Variables;

    if (string.IsNullOrWhiteSpace(subject))
    {
        context.Fail("Missing variables input to use as event subject.");
        return;
    }

    if (!variables.TryGetValue(Parameters.Start, out string? start))
    {
        context.Fail($"Missing variable {Parameters.Start}.");
        return;
    }

    if (!variables.TryGetValue(Parameters.End, out string? end))
    {
        context.Fail($"Missing variable {Parameters.End}.");
        return;
    }

    CalendarEvent calendarEvent = new()
    {
        Subject = variables.Input,
        Start = DateTimeOffset.Parse(start, CultureInfo.InvariantCulture.DateTimeFormat),
        End = DateTimeOffset.Parse(end, CultureInfo.InvariantCulture.DateTimeFormat)
    };

    if (variables.TryGetValue(Parameters.Location, out string? location))
    {
        calendarEvent.Location = location;
    }

    if (variables.TryGetValue(Parameters.Content, out string? content))
    {
        calendarEvent.Content = content;
    }

    if (variables.TryGetValue(Parameters.Attendees, out string? attendees))
    {
        calendarEvent.Attendees = attendees.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
    }

    this._logger.LogInformation("Adding calendar event '{0}'", calendarEvent.Subject);
    await this._connector.AddEventAsync(calendarEvent).ConfigureAwait(false);
}
```

_After_:

```C#
[SKFunction, Description("Add an event to my calendar.")]
public async Task AddEventAsync(
    [Description("Event subject"), SKName("input")] string subject,
    [Description("Event start date/time as DateTimeOffset")] DateTimeOffset start,
    [Description("Event end date/time as DateTimeOffset")] DateTimeOffset end,
    [Description("Event location (optional)")] string? location = null,
    [Description("Event content/body (optional)")] string? content = null,
    [Description("Event attendees, separated by ',' or ';'.")] string? attendees = null)
{
    if (string.IsNullOrWhiteSpace(subject))
    {
        throw new ArgumentException($"{nameof(subject)} variable was null or whitespace", nameof(subject));
    }

    CalendarEvent calendarEvent = new()
    {
        Subject = subject,
        Start = start,
        End = end,
        Location = location,
        Content = content,
        Attendees = attendees is not null ? attendees.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries) : Enumerable.Empty<string>(),
    };

    this._logger.LogInformation("Adding calendar event '{0}'", calendarEvent.Subject);
    await this._connector.AddEventAsync(calendarEvent).ConfigureAwait(false);
}
```
