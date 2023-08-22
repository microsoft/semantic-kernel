---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 6/16/2023
deciders: shawncal, hario90
consulted: dmytrostruk, matthewbolanos 
informed: lemillermicrosoft
---
# Add support for multiple named arguments in template function calls

## Context and Problem Statement

Native functions now support multiple parameters, populated from context values with the same name. Semantic functions currently only support calling native functions with no more than 1 argument. The purpose of these changes is to add support for calling native functions within semantic functions with multiple named arguments.

<!-- This is an optional element. Feel free to remove. -->
## Decision Drivers

* Parity with Guidance
* Similarity to languages familiar to SK developers  
* Readability
* YAML compatibility

## Considered Options

### Syntax idea 1: Using commas
  
```handlebars
{{Skill.MyFunction street: "123 Main St", zip: "98123", city:"Seattle", age: 25}}
```

Pros:

* Commas could make longer function calls easier to read, especially if spaces before and after the arg separator (a colon in this case) are allowed.

Cons:

* Guidance doesn't use commas
* Spaces are already used as delimiters elsewhere so the added complexity of supporting commas isn't necessary

### Syntax idea 2: JavaScript/C#-Style delimiter (colon)
  
```handlebars

{{MyFunction street:"123 Main St" zip:"98123" city:"Seattle" age: "25"}}

```

Pros:

* Resembles JavaScript Object syntax and C# named argument syntax

Cons:

* Doesn't align with Guidance syntax which uses equal signs as arg part delimiters
* Too similar to YAML key/value pairs if we support YAML prompts in the future. It's likely possible to support colons as delimiters but would be better to have a separator that is distinct from normal YAML syntax.

### Syntax idea 3: Python/Guidance-Style delimiter

```handlebars
{{MyFunction street="123 Main St" zip="98123" city="Seattle"}}
```

Pros:

* Resembles Python's keyword argument syntax
* Resembles Guidance's named argument syntax
* Not too similar to YAML key/value pairs if we support YAML prompts in the future.

Cons:

* Doesn't align with C# syntax

### Syntax idea 4: Allow whitespace between arg name/value delimiter

```handlebars
{{MyFunction street = "123 Main St" zip   = "98123" city = "Seattle"}}
```

Pros:

* Follows the convention followed by many programming languages of whitespace flexibility where spaces, tabs, and newlines within code don't impact a program's functionality

Cons:

* Promotes code that is harder to read unless commas can be used (see [Using Commas](#syntax-idea-1-using-commas))
* More complexity to support

## Decision Outcome

Chosen options: "Syntax idea 3: Python/Guidance-Style keyword arguments", because it aligns well with Guidance's syntax and is the most compatible with YAML.

Additional decisions:

* Continue supporting up to 1 positional argument for backward compatibility. Currently, the argument passed to a function is assumed to be the `$input` context variable.

Example

```handlebars

{{MyFunction "inputVal" street="123 Main St" zip="98123" city="Seattle"}}

```

* Don't allow whitespace before and after equals sign for named args because without commas, differentiating between arguments becomes more difficult to read.
* Arg values are allowed to be defined as strings or variables ONLY, e.g.
  
```handlebars
{{MyFunction street=$street zip="98123" city='Seattle'}}
```

If function expects a value other than a string for an argument, the SDK will use the corresponding TypeConverter to parse the string provided when evaluating the expression.

