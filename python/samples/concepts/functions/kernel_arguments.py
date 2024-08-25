# Copyright (c) Microsoft. All rights reserved.


import asyncio
import datetime
import locale
from typing import Annotated

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

# This example shows how to use kernel arguments when invoking functions.


class StaticTextPlugin:
    """A plugin for generating static text."""

    @kernel_function(name="uppercase", description="Convert text to uppercase")
    def uppercase(
        self, text: Annotated[str, "The input text"]
    ) -> Annotated[str, "The output is the text in uppercase"]:
        """Convert text to uppercase.

        Args:
            text (str): The text to convert to uppercase.

        Returns:
            str: The text in uppercase.
        """
        return text.upper()

    @kernel_function(name="append_day", description="Append the day variable")
    def append_day(
        self,
        input: Annotated[str, "The input text"],
        day: Annotated[str, "The day to append"],
    ) -> Annotated[str, "The output is the text with the day appended"]:
        """Append the day variable.

        Args:
            input (str): The input text to append the day to.
            day (str): The day to append.

        Returns:
            str: The text with the day appended.
        """
        return f"{input} {day}"


def get_day_of_week_for_locale():
    """Get the day of the week for the current locale."""
    locale.setlocale(locale.LC_TIME, "")
    return datetime.datetime.now().strftime("%A")


async def main():
    kernel = Kernel()

    text_plugin = kernel.add_plugin(StaticTextPlugin(), "TextPlugin")
    arguments = KernelArguments(input="Today is:", day=get_day_of_week_for_locale())

    result = await kernel.invoke(text_plugin["append_day"], arguments)

    # The result returned is of type FunctionResult. Printing the result calls the __str__ method.
    print(result)

    # Note: if you need access to the result metadata, you can do the following
    # metadata = result.metadata


if __name__ == "__main__":
    asyncio.run(main())
