---
# These are optional elements. Feel free to remove any of them.
status: { proposed }
contact: { Eduard van Valkenburg }
date: { 2024-06-14 }
deciders: { Eduard van Valkenburg, Ben Thomas, Evan Mattson, Matthew Bolanos }
consulted: { Ben Thomas, Evan Mattson, Gil LaHaye, Tao Chen, Matthew Bolanos }
---

# Pythonic design principles

## Context and Problem Statement

The Pythonic design principles are a set of guidelines that help developers write code that is idiomatic to the Python programming language, while maintaining similar concepts as the dotnet version of Semantic Kernel. These principles are not strict rules, but rather a set of best practices that help developers write code that is easy to read, write, and maintain, and helps decide when and how to deviate from a design set forth for dotnet.

While we try to maintain parity between dotnet, python and java for Semantic Kernel, it is also important to allow for language-specific idioms and best practices to be followed. This decision will help guide the development of the Python version of Semantic Kernel.

## Context
There are some structural differences between dotnet and python that bear a closer look, as they have a large effect on designing python applications vs designing dotnet applications. These differences include:
- Inheritance
  - in dotnet a class can only inherit from one class, while in python a class can inherit from any number of other classes
  - in dotnet interfaces play a major role, while in python a interface does not exist, they can be replicated with abstract base classes (ABC's) and somewhat with Protocols, but those are not the same, for instance a ABC can have implemented methods, while an interface cannot.
  - further a regular class can have a abstract method, which is not implemented, making the class act like a ABC without explicitly being one.
  - python protocols are a way to define a interface, but they are not enforced, they can be checked at runtime and will be used by type checker, but the developer does not have to worry about them, they can implement their class that adheres to the protocol without explicitly stating that it does.
  - a developer can also take any existing class and subclass it and change one or more methods within it, without having to reimplement everything that is in the original class, this is also a quite common pattern in python and one of the reasons that python is so flexible and didn't introduce interfaces (and ABC and Protocols only in later versions).
- Dependency Injection
  - In python everything is a object, which includes classes and functions, this means that dependency injection can be done by passing a function as a parameter to another function, or by passing a class as a parameter to another class, and this is a very common pattern in python, there isn't even really a name for it.
- Typing
  - While python is untyped, it is a best practice to type everything and we do, and we check those types using mypy.
- Private vs Public
  - In python there is no private or protected, everything is public, but there is a convention to use a single underscore to denote a private method or variable, and a double underscore to denote a protected method or variable, but this is only a convention and not enforced by the language.
- Sealed classes
  - In python there is no such thing as a sealed class, and it is also uncommon for a class to be defined within another class, this is a common pattern in dotnet, but not in python.
- Internal static classes
  - Since everything is an object in python, there is no need for a internal static class. 
  - Defining the functions within a file and directly importing the functions is a common pattern in python, and is used in the current codebase. 

## Design Principles
These are not generic Python design principles, but rather principles that are specific to the Semantic Kernel project. The zen of python can be found [here](https://peps.python.org/pep-0020/).
1. **Base classes and interfaces can be skipped**
   - Since it is not necessary to define a base class, there are good reasons to skip them
   - One example in the current codebase is the [AIServiceSelector](/python/semantic_kernel/services/ai_service_selector.py) class, it is a simple class with a single method, and developers can override that method after subclassing the AIServiceSelector, no need to subclass a base class instead. 
   - There are other cases where a base class does add value, like the [AIServiceClientBase](/python/semantic_kernel/services/ai_service_client_base.py) class, which has a lot of shared functionality, and is a good example of a base class that is widely implemented by different services.
1. **Dependency injection can be replaced with passing a class and optionally combined with a generic**
   - Whenever dependency injection is used in a dotnet design, similar effects can be achieved by passing a class or a instance of a class as a parameter to another class or function, this is a common pattern in python and is used in the current codebase.
   - Generic classes in python do have more to do with typing, so they are not a full replacement of dependency injection, but they can be used in concert with passing a class.
   - Generic functions are not yet supported until python 3.12, and since we support python 3.10 and up, we will not use them yet, alternatives are passing a class to a function, using a parameter, or combining that with a singledispatch structure.
1. **We hold the convention that a private function or variable is denoted by a single underscore**
   - This is a common convention in python, and is used in the current codebase.
   - This is not enforced by the language, but is a good practice to follow.
   - This will make it easier to understand similar functions or variables in the codebase.
1. **Sealed, internal classes are replaced with regular classes**
    - Since there are no sealed nor internal classes, we will use regular classes instead.
    - They should not be defined within another class as that is not a common pattern in python and makes the code harder to read.
1. **Internal static classes are not replicated, functions are defined within a file and imported directly**
    - Since everything is an object in python, there is no need for a internal static class.
    - Defining the functions within a file and directly importing the functions is a common pattern in python, and is used in the current codebase.
    - This makes the code easier to read and understand.
    - The only exception is when there is actually shared state between the functions, in that case a class can be used.

## Conclusion
There is no silver bullet when it comes to translating the dotnet design to python, these principles will help guide the discussion and are likely to be updated as we go.