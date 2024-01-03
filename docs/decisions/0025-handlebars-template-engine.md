---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: teresaqhoang
date: 2023-12-06
deciders: markwallace, alliscode, SergeyMenshykh
consulted: markwallace, mabolan
informed: stephentoub
---

# Handlebars Prompt Template Helpers

## Context and Problem Statement

We want to use Handlebars as a template factory for rendering prompts and planners in the Semantic Kernel. Handlebars provides a simple and expressive syntax for creating dynamic templates with logic and data. However, Handlebars does not have built-in support for some features and scenarios that are relevant for our use cases, such as:

- Marking a block of text as a message with a role for chat completion connectors.
- Invoking functions from the kernel and passing parameters to them.
- Setting and getting variables in the template context.
- Performing common operations such as concatenation, arithmetic, comparison, and JSON serialization.
- Supporting different output types and formats for the rendered template.

Therefore, we need to extend Handlebars with custom helpers that can address these gaps and provide a consistent and convenient way for prompt and planner engineers to write templates.

First, we will do this by **_baking in a defined set of custom system helpers_** for common operations and utilities that are not provided any the built-in Handlebars helpers, which:

- Allows us full control over what functionality can be executed by the Handlebars template factory.
- Enhances the functionality and usability of the template factory, by providing helpers for common operations and utilities that are not provided by any built-in Handlebars helpers but are commonly hallucinated by the model.
- Improves the expressiveness and readability of the rendered template, as the helpers can be used to perform simple or complex logic or transformations on the template data / arguments.
- Provides flexibility and convenience for the users, as they can:

  - Choose the syntax, and
  - Extend, add, or omit certain helpers

  to best suits their needs and preferences.

- Allows for customization of specific operations or utilities that may have different behavior or requirements, such as handling output types, formats, or errors.

These helpers would handle the evaluation of the arguments, the execution of the operation or utility, and the writing of the result to the template. Examples of such operations are `{{concat string1 string2 ...}}`, `{{equal value1 value2}}`, `{{json object}}`, `{{set name=value}}`, `{{get name}}`, `{{or condition1 condition2}}`, etc.

Secondly, we have to **_expose the functions that are registered in the Kernel as helpers_** to the Handlebars template factory. Options for this are detailed below.

## Decision Drivers

- We want to leverage the existing Handlebars helpers, syntax, and mechanisms for loading helpers as much as possible, without introducing unnecessary complexity or inconsistency.
- We want to provide helpers that are useful and intuitive for prompt and SK engineers.
- We want to ensure that the helpers are well-documented, tested, and maintained, and that they do not conflict with each other or with the built-in Handlebars helpers.
- We want to support different output types and formats for the rendered template, such as text, JSON, or complex objects, and allow the template to specify the desired output type.

## Considered Options

We considered the following options for extending Handlebars with kernel functions as custom helpers:

**1. Use a single helper for invoking functions from the kernel.** This option would use a generic helper, such as `{{invoke pluginName-functionName param1=value1 param2=value2 ...}}`, to call any function from the kernel and pass parameters to it. The helper would handle the execution of the function, the conversion of the parameters and the result, and the writing of the result to the template.

**2. Use a separate helper for each function from the kernel.** This option would register a new helper for each function, such as `{{pluginName-functionName param1=value1 param2=value2 ...}}`, to handle the execution of the function, the conversion of the parameters and the result, and the writing of the result to the template.

## Pros and Cons

### 1. Use a single generic helper for invoking functions from the kernel

Pros:

- Simplifies the registration and maintenance of the helper, as only one helper, `invoke`, needs to be defined and updated.
- Provides a consistent and uniform syntax for calling any function from the kernel, regardless of the plugin or function name, parameter details, or the result.
- Allows for customization and special logic of kernel functions, such as handling output types, execution restrictions, or errors.
- Allows the use of positional or named arguments, as well as hash arguments, for passing parameters to the function.

Cons:

- Reduces the expressiveness and readability of the template, as the function name and parameters are wrapped in a generic helper invocation.
- Adds additional syntax for the model to learn and keep track of, potentially leading to more errors during render.

### 2. Use a generic helper for _each_ function from the kernel

Pros:

- Has all the benefits of option 1, but largely improves the expressiveness and readability of the template, as the function name and parameters are directly written in the template.
- Maintains ease of maintenance for handling each function, as each helper will follow the same templated logic for registration and execution.

Cons:

- May cause conflicts or confusion with the built-in Handlebars helpers or the kernel variables, if the function name or the parameter name matches them.

## Decision Outcome

We decided to go with option 2: providing special helpers to invoke any function in the kernel. These helpers will follow the same logic and syntax for each registered function. We believe that this approach, alongside the custom system helpers that will enable special utility logic or behavior, provides the best balance between simplicity, expressiveness, flexibility, and functionality for the Handlebars template factory and our users.

With this approach,

- We will allow customers to use any of the built-in [Handlebars.Net helpers](https://github.com/Handlebars-Net/Handlebars.Net.Helpers).
- We will provide utility helpers, which are registered by default.
- We will provide prompt helpers (e.g. chat message), which are registered by default.
- We will register all plugin functions registered on the `Kernel`.
- We will allow customers to control which plugins are registered as helpers and the syntax of helpers' signatures.
  - By default, we will honor all options defined in [HandlebarsHelperOptions](https://github.com/Handlebars-Net/Handlebars.Net.Helpers/blob/8f7c9c082e18845f6a620bbe34bf4607dcba405b/src/Handlebars.Net.Helpers/Options/HandlebarsHelpersOptions.cs#L12).
  - Additionally, we will extend this configuration to include a `RegisterCustomHelpersCallback` option that users can set to register custom helpers.
- We will allow Kernel function arguments to be easily accessed, i.e., function variables and execution settings, via a `KernelArguments` object.
- We will allow customers to control when plugin functions are registered as helpers.
  - By default, this is done when template is rendered.
  - Optionally, this can be done when the Handlebars template factory is constructed by passing in a Plugin collection.
- If conflicts arise between built-in helpers, variables, or kernel objects:
  - We will throw an error clearly explaining what the issue is, as well as
  - Allow customers to provide their own implementations and overrides, including an option to not register default helpers. This can be done by setting `Options.Categories` to an empty array `[]`.

We also decided to follow some guidelines and best practices for designing and implementing the helpers, such as:

- Documenting the purpose, syntax, parameters, and behavior of each helper, and providing examples and tests for them.
- Naming the helpers in a clear and consistent way, and avoiding conflicts or confusion with the built-in Handlebars helpers or the kernel functions or variables.
  - Using standalone function names for custom system helpers (i.e., json, set)
  - Using the delimiter "`-`" for helpers registered to handle the kernel functions, to distinguish them from each other and from our system or built-in Handlebars helpers.
- Supporting both positional and hash arguments, for passing parameters to the helpers, and validating the arguments for the required type and count.
- Handling the output types, formats, and errors of the helpers, including complex types or JSON schemas.
- Implementing the helpers in a performant and secure way, and avoiding any side effects or unwanted modifications to the template context or data.

Effectively, there will be four buckets of helpers enabled in the Handlebars Template Engine:

1. Default helpers from the Handlebars library, including:
   - [Built-in helpers](https://handlebarsjs.com/guide/builtin-helpers.html) that enable loops and conditions (#if, #each, #with, #unless)
   - [Handlebars.Net.Helpers](https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki)
2. Functions in the kernel
3. Helpers helpful to prompt engineers (i.e., message, or)
4. Utility helpers that can be used to perform simple logic or transformations on the template data or arguments (i.e., set, get, json, concat, equals, range, array)

### Pseudocode for the Handlebars Prompt Template Engine

A prototype implementation of a Handlebars prompt template factory with built-in helpers could look something like this:

```csharp
/// Options for Handlebars helpers (built-in and custom).
public sealed class HandlebarsPromptTemplateOptions : HandlebarsHelpersOptions
{
  // Categories tracking built-in system helpers
  public enum KernelHelperCategories
  {
    Prompt,
    Plugin,
    Context,
    String,
    ...
  }

  /// Default character to use for delimiting plugin name and function name in a Handlebars template.
  public string DefaultNameDelimiter { get; set; } = "-";

  /// Delegate for registering custom helpers.
  public delegate void RegisterCustomHelpersCallback(IHandlebars handlebarsInstance, KernelArguments executionContext);

  /// Callback for registering custom helpers.
  public RegisterCustomHelpersCallback? RegisterCustomHelpers { get; set; } = null;

  // Pseudocode, some combination of both KernelHelperCategories and the default HandlebarsHelpersOptions.Categories.
  public List<Enum> AllCategories = KernelHelperCategories.AddRange(Categories);
}
```

```csharp
// Handlebars Prompt Template
internal class HandlebarsPromptTemplate : IPromptTemplate
{
  public async Task<string> RenderAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken = default)
  {
    arguments ??= new();
    var handlebarsInstance = HandlebarsDotNet.Handlebars.Create();

    // Add helpers for kernel functions
    KernelFunctionHelpers.Register(handlebarsInstance, kernel, arguments, this._options.PrefixSeparator, cancellationToken);

    // Add built-in system helpers
    KernelSystemHelpers.Register(handlebarsInstance, arguments, this._options);

    // Register any custom helpers
    if (this._options.RegisterCustomHelpers is not null)
    {
      this._options.RegisterCustomHelpers(handlebarsInstance, arguments);
    }
    ...

    return await Task.FromResult(prompt).ConfigureAwait(true);
  }
}

```

```csharp
/// Extension class to register Kernel functions as helpers.
public static class KernelFunctionHelpers
{
  public static void Register(
    IHandlebars handlebarsInstance,
    Kernel kernel,
    KernelArguments executionContext,
    string nameDelimiter,
    CancellationToken cancellationToken = default)
  {
      kernel.Plugins.GetFunctionsMetadata().ToList()
          .ForEach(function =>
              RegisterFunctionAsHelper(kernel, executionContext, handlebarsInstance, function, nameDelimiter, cancellationToken)
          );
  }

  private static void RegisterFunctionAsHelper(
    Kernel kernel,
    KernelArguments executionContext,
    IHandlebars handlebarsInstance,
    KernelFunctionMetadata functionMetadata,
    string nameDelimiter,
    CancellationToken cancellationToken = default)
  {
    // Register helper for each function
    handlebarsInstance.RegisterHelper(fullyResolvedFunctionName, (in HelperOptions options, in Context context, in Arguments handlebarsArguments) =>
    {
      // Get parameters from template arguments; check for required parameters + type match

      // If HashParameterDictionary
      ProcessHashArguments(functionMetadata, executionContext, handlebarsArguments[0] as IDictionary<string, object>, nameDelimiter);

      // Else
      ProcessPositionalArguments(functionMetadata, executionContext, handlebarsArguments);

      KernelFunction function = kernel.Plugins.GetFunction(functionMetadata.PluginName, functionMetadata.Name);

      InvokeSKFunction(kernel, function, GetKernelArguments(executionContext), cancellationToken);
    });
  }
  ...
}
```

```csharp
/// Extension class to register additional helpers as Kernel System helpers.
public static class KernelSystemHelpers
{
    public static void Register(IHandlebars handlebarsInstance, KernelArguments arguments, HandlebarsPromptTemplateOptions options)
    {
        RegisterHandlebarsDotNetHelpers(handlebarsInstance, options);
        RegisterSystemHelpers(handlebarsInstance, arguments, options);
    }

    // Registering all helpers provided by https://github.com/Handlebars-Net/Handlebars.Net.Helpers.
    private static void RegisterHandlebarsDotNetHelpers(IHandlebars handlebarsInstance, HandlebarsPromptTemplateOptions helperOptions)
    {
        HandlebarsHelpers.Register(handlebarsInstance, optionsCallback: options =>
        {
            ...helperOptions
        });
    }

    // Registering all helpers built by the SK team to support the kernel.
    private static void RegisterSystemHelpers(
      IHandlebars handlebarsInstance, KernelArguments arguments, HandlebarsPromptTemplateOptions helperOptions)
    {
      // Where each built-in helper will have its own defined class, following the same pattern that is used by Handlebars.Net.Helpers.
      // https://github.com/Handlebars-Net/Handlebars.Net.Helpers
      if (helperOptions.AllCategories contains helperCategory)
      ...
      KernelPromptHelpers.Register(handlebarsContext);
      KernelPluginHelpers.Register(handlebarsContext);
      KernelStringHelpers..Register(handlebarsContext);
      ...
    }
}
```

**Note: This is just a prototype implementation for illustration purposes only.**

Handlebars supports different object types as variables on render. This opens up the option to use objects outright rather than just strings in semantic functions, i.e., loop over arrays or access properties of complex objects, without serializing or deserializing objects before invocation.
