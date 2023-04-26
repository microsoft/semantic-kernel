import semantic_kernel as sk


async def summarize_function_test(kernel: sk.Kernel):
    # Define semantic function using SK prompt template language
    sk_prompt = """
    {{$input}}
    {{$input2}}

    Give me the TLDR in exactly 5 words:
    """

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=200, temperature=0, top_p=0.5
    )

    # User input
    text_to_summarize = """
        1) A robot may not injure a human being or, through inaction,
        allow a human being to come to harm.

        2) A robot must obey orders given it by human beings except where
        such orders would conflict with the First Law.

        3) A robot must protect its own existence as long as such protection
        does not conflict with the First or Second Law.
    """

    print("Summarizing: ")
    print(text_to_summarize)
    print()

    # Summarize input string and print
    summary = await kernel.run_async(tldr_function, input_str=text_to_summarize)

    output = str(summary).strip()
    print(f"Summary using input string: '{output}'")
    assert len(output.split(" ")) == 5

    # Summarize input as context variable and print
    context_vars = sk.ContextVariables(text_to_summarize)
    summary = await kernel.run_async(tldr_function, input_vars=context_vars)

    output = str(summary).strip()
    print(f"Summary using context variables: '{output}'")
    assert len(output.split(" ")) == 5

    # Summarize input context and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    summary = await kernel.run_async(tldr_function, input_context=context)

    output = str(summary).strip()
    print(f"Summary using input context: '{output}'")
    assert len(output.split(" ")) == 5

    # Summarize input context with additional variables and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    context_vars = sk.ContextVariables("4) All birds are robots.")
    summary = await kernel.run_async(
        tldr_function, input_context=context, input_vars=context_vars
    )

    output = str(summary).strip()
    print(f"Summary using context and additional variables: '{output}'")
    assert len(output.split(" ")) == 5

    # Summarize input context with additional input string and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    summary = await kernel.run_async(
        tldr_function, input_context=context, input_str="4) All birds are robots."
    )

    output = str(summary).strip()
    print(f"Summary using context and additional string: '{output}'")
    assert len(output.split(" ")) == 5

    # Summarize input context with additional variables and string and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    context_vars = sk.ContextVariables(variables={"input2": "4) All birds are robots."})
    summary = await kernel.run_async(
        tldr_function,
        input_context=context,
        input_vars=context_vars,
        input_str="new text",
    )

    output = str(summary).strip()
    print(
        f"Summary using context, additional variables, and additional string: '{output}'"
    )
    assert len(output.split(" ")) == 5
