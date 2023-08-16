---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 6/16/2023
deciders: shawncal, hario90
consulted: dmytrostruk {list everyone whose opinions are sought (typically subject-matter experts); and with whom there is a two-way communication}
informed: {list everyone who is kept up-to-date on progress; and with whom there is a one-way communication}
---
# Add support for multiple named arguments in template function calls

## Context and Problem Statement

Native functions now support multiple parameters, populated from context values with the same name. Semantic functions currently only support calling native functions with no more than 1 argument. The purpose of these changes is to add support for calling native functions within semantic functions with multiple named arguments.

<!-- This is an optional element. Feel free to remove. -->
## Decision Drivers


* {decision driver 1, e.g., a force, facing concern, …}
* {decision driver 2, e.g., a force, facing concern, …}
* … <!-- numbers of drivers can vary -->

## Considered Options

* Support the following syntax for named arguments:
  
```handlebars
{{MyFunction street:"123 Main St", zip:"98123", city:"Seattle"}}
```

* {title of option 2}
* {title of option 3}
* … <!-- numbers of options can vary -->

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.
