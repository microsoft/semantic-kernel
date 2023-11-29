---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: teresaqhoang
date: 2023-11-21
deciders: markwallace, mabolan, alliscode, SergeyMenshykh, dluc
consulted: markwallace, mabolan
informed:
---

# Handlebars Planner Template Engine Helpers

## Context and Problem Statement

We want to use Handlebars as a template engine for rendering prompts and planners in the Semantic Kernel. Handlebars provides a simple and expressive syntax for creating dynamic templates with logic and data. However, Handlebars does not have built-in support for some features and scenarios that are relevant for our use cases, such as:

- Marking a block of text as a message with a role for chat completion connectors.
- Invoking functions from the kernel and passing parameters to them.
- Setting and getting variables in the template context.
- Performing common operations such as concatenation, arithmetic, comparison, and JSON serialization.
- Supporting different output types and formats for the rendered template.

Therefore, we need to extend Handlebars with custom helpers that can address these gaps and provide a consistent and convenient way for prompt and planner engineers to write templates.

## Decision Drivers

- We want to leverage the existing Handlebars syntax and features as much as possible, without introducing unnecessary complexity or inconsistency.
- We want to provide helpers that are useful and intuitive for prompt and SK engineers.
- We want to ensure that the helpers are well-documented, tested, and maintained, and that they do not conflict with each other or with the built-in Handlebars helpers.
- We want to support different output types and formats for the rendered template, such as text, JSON, or complex objects, and allow the template to specify the desired output type.

## Considered Options

We considered the following options for extending Handlebars with custom helpers:

**1. Use a single helper for invoking functions from the kernel.** This option would use a generic helper, such as `{{invoke pluginName-functionName param1=value1 param2=value2 ...}}`, to call any function from the kernel and pass parameters to it. The helper would handle the execution of the function, the conversion of the parameters and the result, and the writing of the result to the template.

**2. Use a separate helper for each function from the kernel.** This option would register a new helper for each function, such as `{{pluginName-functionName param1=value1 param2=value2 ...}}`, to handle the execution of the function, the conversion of the parameters and the result, and the writing of the result to the template.

**3. Use a defined set of helpers for common operations and utilities.** This option would leverage a set of custom system helpers, such as `{{concat string1 string2 ...}}`, `{{equal value1 value2}}`, `{{json object}}`, `{{set name=value}}`, `{{get name}}`, `{{or condition1 condition2}}`, etc., to perform common operations and utilities that are not provided by the built-in Handlebars helpers or kernel functions. The helpers would handle the evaluation of the arguments, the execution of the operation or utility, and the writing of the result to the template.

## Pros and Cons

**1. Use a single generic helper for invoking functions from the kernel**

Pros:

- Simplifies the registration and maintenance of the helper, as only one helper, `invoke`, needs to be defined and updated.
- Provides a consistent and uniform syntax for calling any function from the kernel, regardless of the plugin or function name, parameter details, or the result.
- Allows for customization and special logic of kernel functions, such as handling output types, execution restrictions, or errors.
- Allows the use of positional or named arguments, as well as hash arguments, for passing parameters to the function.

Cons:

- Reduces the expressiveness and readability of the template, as the function name and parameters are wrapped in a generic helper invocation.
- Adds additional syntax for the model to learn and keep track of, potentially leading to more errors during render.

**2. Use a generic helper for each function from the kernel**

Pros:

- Has all the benefits of option 1, but largely improves the expressiveness and readability of the template, as the function name and parameters are directly written in the template.
- Maintains ease of maintenance for handling each function, as each helper will follow the same templated logic for registration and execution.

Cons:

- May cause conflicts or confusion with the built-in Handlebars helpers or the kernel variables, if the function name or the parameter name matches them.

**3. Use a set of helpers for common operations and utilities**

Pros:

- Allows us full control over what functionality can be executed by the Handlebars template engine.
- Enhances the functionality and usability of the template engine, by providing helpers for common operations and utilities that are not provided by the built-in Handlebars helpers or kernel functions but is commonly hallucinated by the model.
- Improves the expressiveness and readability of the rendered template, as the helpers can be used to perform simple or complex logic or transformations on the template data or arguments.
- Provides flexibility and convenience for the users, as they can choose the syntax and extend or omit certain helpers to best suits their needs and preferences.
- Allows for customization of specific operations or utilities that may have different behavior or requirements, such as handling output types, formats, or errors.

Cons:

- Increases the complexity and maintenance of the helpers, as each helper needs to be defined and updated separately, and may have different logic or behavior.
- May cause conflicts or confusion with the built-in Handlebars helpers or the kernel functions or variables, if the helper name or the argument name matches them.
- May cause inconsistency or confusion for the users, as they may not be aware of the differences or the availability of the helpers, or may use them incorrectly or interchangeably.
- May introduce performance or security issues, if the helpers are not implemented or used correctly or safely.

## Decision Outcome

We decided to go with a combination of options 2 and 3: providing special helpers to invoke any function in the kernel, and custom system helpers to enable special utility logic or behavior. We believe that this approach provides the best balance between simplicity, expressiveness, flexibility, and functionality for the template engine and the users.

We also decided to follow some guidelines and best practices for designing and implementing the helpers, such as:

- Documenting the purpose, syntax, parameters, and behavior of each helper, and providing examples and tests for them.
- Naming the helpers in a clear and consistent way, and avoiding conflicts or confusion with the built-in Handlebars helpers or the kernel functions or variables.
  - Using standalone function names for custom system helpers (i.e., json, set)
  - Using the delimiter "`-`" for helpers registered to handle the kernel functions, to distinguish them from each other and from our system or built-in Handlebars helpers.
- Supporting both positional and hash arguments, for passing parameters to the helpers, and validating the arguments for the required type and count.
- Handling the output types, formats, and errors of the helpers, including complex types or JSON schemas.
- Implementing the helpers in a performant and secure way, and avoiding any side effects or unwanted modifications to the template context or data.

Effectively, there will be four buckets of helpers enabled in the Handlebars Template Engine:

1. Default helpers from the Handlebars library to enable loops and conditions (#if, #each, #with, #unless)
2. Functions in the kernel
3. Helpers helpful to prompt engineers (i.e., message, or)
4. Utility helpers that can be used to perform simple logic or transformations on the template data or arguments (i.e., set, get, json, concat, equals, range, array)

**HandlebarsPromptTemplate pseudocode**

A prototype implementation of a handlebars prompt template engine with built-in helpers could look something like this:

```csharp
public async Task<string> RenderAsync(Kernel kernel, ContextVariables contextVariables, CancellationToken cancellationToken = default)
{
  return RenderAsync(kernel, contextVariables, new Dictionary<string, object?>(), cancellationToken);
}

// Overloaded method to support a dict of objects as template variables
public async Task<string> RenderAsync(Kernel kernel, ContextVariables contextVariables, Dictionary<string, object?> templateVariables, CancellationToken cancellationToken = default)
{
  var handlebars = HandlebarsDotNet.Handlebars.Create();

  RegisterKernelFunctionsAsHelpers(kernel, contextVariables, handlebars, templateVariables);

  RegisterSystemHelpers(handlebars, templateVariables);

  var template = handlebars.Compile(this._promptModel.Template);

  var prompt = template(templateVariables);

  return await Task.FromResult(prompt).ConfigureAwait(true);
}

private static void RegisterKernelFunctionsAsHelpers(
  Kernel kernel,
  ContextVariables contextVariables,
  IHandlebars handlebarsInstance,
  Dictionary<string, object?> templateVariables,
  CancellationToken cancellationToken = default)
{
  foreach (IKernelPlugin plugin in kernel.Plugins)
  {
      foreach (KernelFunction function in plugin)
      {
        handlebarsInstance.RegisterHelper($"{plugin.Name}-{function.Name}", (in HelperOptions options, in Context context, in Arguments arguments)) =>
        {
          // 1. Get parameters from HB template arguments
          // 2. Port parameter values to context variables
          // 3. Invoke kernel function and write result to the template
        }
      }
  }

}

private static void RegisterSystemHelpers(
    IHandlebars handlebarsInstance,
    Dictionary<string, object?> templateVariables
)
{
  handlebarsInstance.RegisterHelper("customBuiltInHelper1", (in HelperOptions options, in Context context, in Arguments arguments) =>
  {
    ...
  });

  handlebarsInstance.RegisterHelper("customBuiltInHelper2", (in HelperOptions options, in Context context, in Arguments arguments) =>
  {
    ...
  });

  ...
}
```

**Note: This is just a prototype implementation for illustration purposes only.**

Handlebars supports different object types as variables on render. This opens up the option to use objects outright rather than just strings in semantic functions, i.e., loop over arrays or access properties of complex objects, without serializing or deserializing objects before invocation.
