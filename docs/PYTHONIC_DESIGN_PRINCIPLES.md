---
contact: { Eduard van Valkenburg }
last updated: { 2024-08-06 }
---

# Pythonic Design Principles for Semantic Kernel

## Context and Problem Statement

The Pythonic design principles are a set of guidelines that help developers write code that is idiomatic to the Python programming language, while maintaining similar concepts as the dotnet version of Semantic Kernel. These principles are not strict rules, but rather a set of best practices that help developers write code that is easy to read, write, and maintain, and helps decide when and how to deviate from a design set forth for dotnet, as well as vice versa.

While we try to maintain parity between dotnet, python and java for Semantic Kernel, it is also important to allow for language-specific idioms and for best practices to be followed. This decision will help guide the development of the Python version of Semantic Kernel.

## Context
There are some structural differences between dotnet and python that bear a closer look, as they have a large effect on designing python applications vs. designing dotnet applications. These differences include:
- Inheritance
  - in dotnet a class can only inherit from one class, while in python a class can inherit from any number of other classes
  - in dotnet interfaces play a major role, while in python a interface as such does not exist, they can be replicated with abstract base classes (ABC's) and somewhat with Protocols, but those are not the same, for instance a ABC can have implemented methods, while an interface cannot.
  - further a regular class can have a abstract method, which is not implemented, making the class act like a ABC without explicitly being one.
  - python protocols are a way to define a interface, but they are not enforced but used for duck-typing, so that they can be checked at runtime as well as by type checkers, but the developer does not have to worry about them, they can implement their class that adheres to the protocol without explicitly stating that it does, in other words, if it quacks like a duck it is treated as a duck.
  - a developer can also take any existing class and subclass it and change one or more methods within it, without having to reimplement everything that is in the original class, this is also a quite common pattern in python and one of the reasons that python is so flexible and didn't introduce interfaces (and ABC and Protocols only in later versions).
- Dependency Injection
  - In python everything is a object, which includes classes and functions, this means that dependency injection can be done by passing a function as a parameter to another function, or by passing a class as a parameter to another class, and this is a very common pattern in python, there isn't even really a name for it.
  - There are some packages out there that replicate the behavior of dependency injection, but they are not as widely used, and are not needed for the current codebase.
- Typing
  - While python is untyped, it is a best practice to type everything and we do, and we check those types using mypy.
- Private vs Public
  - In python there is no private or protected, everything is public, but there is a convention to use a single underscore to denote a private method or variable, and a double underscore to denote a protected method or variable, but this is only a convention and not enforced by the language.
- Sealed classes
  - In python there is no such thing as a sealed class, and it is also uncommon, and often unnecessary for a class to be defined within another class, this is a common pattern in dotnet, but not in python.
- Internal static classes
  - Since everything is an object in python, including functions that are often encapsulated by a internal static class in dotnet, there is no need for a internal static class. 
  - Defining the functions in one place and importing the functions in (multiple) other places is a common pattern in python, and is used in the current codebase.
- Different types of functions/methods
  - In python there are 4 types of functions that are relevant to designs, function (a regular function, defined outside of a class), method (a function defined within a class), classmethod (a method that is bound to the class and not the instance, and can be called on the class itself), and staticmethod (a method that is not bound to the class or the instance, and can be called on the class or the instance).

## Design Principles
These are not generic Python design principles, but rather principles that are specific to the Semantic Kernel project. For more generic python principles, use "The Zen of Python" ([source](https://peps.python.org/pep-0020/)).
1. **The goal of the python version of dotnet designs is not to complete coverage of all classes in the dotnet design.**
   - The goal is to maintain the same functionality and behavior, while adhering to pythonic design principles.
   - This means that in some cases, things like config classes are not implemented, but keyword arguments are used instead, as they are more idiomatic to python, the same with options classes, and many static classes, which are not needed in python.
   - We also build on pydantic for many of the data classes, as it is a widely used and well maintained library that is idiomatic to python and has the added benefit of easily using validation and serialization as well as limiting boiler plate `__init__` code.
1. **Base classes and interfaces can be skipped, as long as SOLID is maintained.**
   - Since a user can subclass any class, a abstract base class is not always needed, as long as SOLID is maintained.
   - There are three ways to provide the same behavior to SK users in python, compared to dotnet:
     - Subclassing a concrete class and overriding a method.
       - One example in the current codebase is the [AIServiceSelector](../python/semantic_kernel/services/ai_service_selector.py) class, it is a simple class with a single method, and developers can override that method by creating a subclass of the AIServiceSelector, so there is no need to subclass a base class instead, it is then passed into the Kernel class and used instead of the default implementation.
     - Subclassing a (abstract) base class and implementing all required methods.
       - A base class adds value when they are used extensively throughout the core code, i.e. the [AIServiceClientBase](../python/semantic_kernel/services/ai_service_client_base.py) class, which has a lot of shared functionality, and is a good example of a base class that is widely implemented by different services.
       - One note, is that while it is common to use ABC as the base class, this is not always the case, a regular class with a default implementation, or one or more abstractmethods can be used instead.
     - Runtime checking using a protocol.
       - For cases where the developer is the primary creator of subclasses, and we want to make it easy while still enforcing methods and signatures, we can use a protocol, which can be used for type checking as well as runtime checks.
   - Given the dynamic nature of python all three of these approaches allow us to use dependency inversion, as long as we make sure function calls and constructors allow either passing of the  class, a implementation of that class or uses a `classmethod` to allow different approaches to create objects.
   - Another case that bears a note is when in dotnet multiple interfaces are combined into larger interfaces, that is not needed in python as it creates unnecessary nesting and complexity, a class can inherit from multiple classes and that is enough, it might even be the case that the core functionality is done through a base class, while some of the smaller parts are only runtime checked by a protocol, but some judgement is needed here, the most important consideration is who will be doing the bulk of the subclassing, if it is the developer, a protocol is likely the best choice, if it is the core team, a base class is likely the best choice.
     - A second level base class that only combines two or more other base classes without adding any implementation should not be used, as it is not needed and adds complexity.
2. **Dependency injection can be replaced with passing a class and optionally combined with a generic**
   - Whenever dependency injection is used in a dotnet design, the same setup can be done in python, the difference being that a explicit framework and a factory method are not needed, making sure instances of classes created within other classes, are adaptable should be enough for most use cases.
   - Generic classes in python have more to do with typing, so they are not a full replacement of dependency injection, but they can be used in concert with passing a class.
   - Generic functions are not yet supported until python 3.12, and since we support python 3.10 and up, we will not use them yet, alternatives are passing a class to a function, using a parameter, or combining that with a `singledispatch` structure.
3. **We hold the convention that a private function or variable is denoted by a single underscore**
   - This is a common convention in python, and is used in the current codebase.
   - This is not enforced by the language, although some IDE's will flag usage of "private" methods, and is a good practice to follow as in makes the code easier to read and understand.
4. **Sealed, internal classes are replaced with regular classes**
    - Since there are no sealed nor explicit internal classes, in python we use regular classes instead.
    - They should not be defined within another class as that is not a common pattern in python and makes the code harder to read, and it breaks the "flat is better then nested" principle.
5. **Internal static classes are not replicated, functions are defined within a file and imported directly**
    - Since everything is an object in python, there is no need for a internal static class.
    - Defining the functions within a file and directly importing the functions is a common pattern in python, and is used in the current codebase.
    - This makes the code easier to read and understand, as the used functions are imported directly and can be more easily traced back to their origin, a internal static class obscures what gets imported and potentially imports unneeded objects.
    - Of course when there is actually shared state between the functions, a class is used.

## Conclusion
There is no silver bullet when it comes to translating the dotnet design to python, these principles will help guide the discussion and are likely to be updated as we go.
