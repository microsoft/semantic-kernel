---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 6/16/2023
deciders: shawncal, hario90
consulted: dmytrostruk {list everyone whose opinions are sought (typically subject-matter experts); and with whom there is a two-way communication}
informed: lemillermicrosoft
---
# Add support for multiple named arguments in template function calls

## Context and Problem Statement

Native functions now support multiple parameters, populated from context values with the same name. Semantic functions currently only support calling native functions with no more than 1 argument. The purpose of these changes is to add support for calling native functions within semantic functions with multiple named arguments.

<!-- This is an optional element. Feel free to remove. -->
## Decision Drivers

* YAML compatibility
* Guidance
* Similarity to languages used by SK developers  
* Ease of use

## Considered Options

### Syntax idea 1: Pseudo JavaScript/C#-style with commas
  
```handlebars
{{Skill.MyFunction street:"123 Main St", zip:"98123", city:"Seattle", age: 25}}
```

Pros:

* commas could make longer function calls easier to read.

Cons:

* commas add implementation/maintenance cost
* spaces are already used as delimiters elsewhere so commas seem unnecessary


### Syntax idea 2: JavaScript/C#-Style without commas
  
```handlebars

{{MyFunction street:"123 Main St" zip:"98123" city:"Seattle" age: "25"}}

```

Pros:

* Resembles JavaScript Object syntax and C# named argument syntax
* Not using commas avoids the Cons in Syntax idea #1.

Cons:

* Doesn't align with Guidance syntax

### Syntax idea 3: Python/Guidance-Style keyword arguments

```handlebars
{{MyFunction street="123 Main St" zip="98123" city="Seattle"}}
```

Pros:

* Resembles Python's keyword argument syntax
* Resembles Guidance's named argument syntax

Cons:

* Doesn't align with C# syntax

### Allow whitespace between arg name/value separator

```handlebars
{{MyFunction street = "123 Main St" zip="98123" city="Seattle"}}
```

Pros:

* Follows the convention followed by many programming languages of whitespace flexibility where spaces, tabs, and newlines within code don't impact a program's functionality

Cons:

* Promotes code that is harder to read
* Harder to support

## Decision Outcome

Chosen option: "Syntax idea 3: Python/Guidance-Style keyword arguments", because it aligns well with Guidance's syntax and TODO.

Additional decisions:

* Continue supporting up to 1 positional argument for backward compatibility. Currently, the argument passed to a function is assumed to be the `$input` context variable.

Example

```handlebars

{{MyFunction "inputVal" street="123 Main St" zip="98123" city="Seattle"}}

```

* Allow whitespace before and after equals sign for named args because spaces are also ignored within curly braces.
* Arg values are allowed to be defined as strings or variables, e.g.
  
```handlebars
{{MyFunction street=$street zip="98123" city='Seattle'}}
```

If function expects a value other than a string for an argument, the SDK will use the corresponding TypeConverter to parse the string provided when evaluating the expression.

Quotes are still required? TODO
