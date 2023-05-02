import semantic_kernel as sk


async def summarize_function_test(kernel: sk.Kernel):
    # Define semantic function using SK prompt template language
    sk_prompt = """
    {{$input}}
    {{$input2}}

    (hyphenated words count as 1 word)
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


async def simple_summarization(kernel: sk.Kernel):
    # Define semantic function using SK prompt template language
    sk_prompt = "{{$input}} {{$input2}}"

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=80, temperature=0, top_p=0.5
    )

    # User input (taken from https://en.wikipedia.org/wiki/Whale)
    text_to_summarize = """
        Whales are fully aquatic, open-ocean animals:
        they can feed, mate, give birth, suckle and raise their young at sea.
        Whales range in size from the 2.6 metres (8.5 ft) and 135 kilograms (298 lb)
        dwarf sperm whale to the 29.9 metres (98 ft) and 190 tonnes (210 short tons) blue whale,
        which is the largest known animal that has ever lived. The sperm whale is the largest
        toothed predator on Earth. Several whale species exhibit sexual dimorphism,
        in that the females are larger than males.
    """
    additional_text = """
        The word "whale" comes from the Old English hwæl, from Proto-Germanic *hwalaz,
        from Proto-Indo-European *(s)kwal-o-, meaning "large sea fish".[3][4]
        The Proto-Germanic *hwalaz is also the source of Old Saxon hwal,
        Old Norse hvalr, hvalfiskr, Swedish val, Middle Dutch wal, walvisc, Dutch walvis,
        Old High German wal, and German Wal.[3] Other archaic English forms include wal,
        wale, whal, whalle, whaille, wheal, etc.[5]
    """

    print("Summarizing: ")
    print(text_to_summarize)
    print()

    # Summarize input string and print
    summary = await kernel.run_async(tldr_function, input_str=text_to_summarize)

    output = str(summary).strip()
    print(f"Summary using input string: '{output}'")
    assert len(output) > 0

    # Summarize input as context variable and print
    context_vars = sk.ContextVariables(text_to_summarize)
    summary = await kernel.run_async(tldr_function, input_vars=context_vars)

    output = str(summary).strip()
    print(f"Summary using context variables: '{output}'")
    assert len(output) > 0

    # Summarize input context and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    summary = await kernel.run_async(tldr_function, input_context=context)

    output = str(summary).strip()
    print(f"Summary using input context: '{output}'")
    assert len(output) > 0

    # Summarize input context with additional variables and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    context_vars = sk.ContextVariables(additional_text)
    summary = await kernel.run_async(
        tldr_function, input_context=context, input_vars=context_vars
    )

    output = str(summary).strip()
    print(f"Summary using context and additional variables: '{output}'")
    assert len(output) > 0

    # Summarize input context with additional input string and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    summary = await kernel.run_async(
        tldr_function, input_context=context, input_str=additional_text
    )

    output = str(summary).strip()
    print(f"Summary using context and additional string: '{output}'")
    assert len(output) > 0

    # Summarize input context with additional variables and string and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    context_vars = sk.ContextVariables(variables={"input2": additional_text})
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
    assert len(output) > 0


async def simple_completion(kernel: sk.Kernel):
    # Define semantic function using SK prompt template language
    sk_prompt = "Hello, I like {{$input}}{{$input2}}"

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=25, temperature=0.7, top_p=0.5
    )

    # User input
    simple_input = "sleeping and "

    print("Completing: ")
    print()

    # Complete input string and print
    summary = await kernel.run_async(tldr_function, input_str=simple_input)

    output = str(summary).strip()
    print(f"Completion using input string: '{output}'")
    assert len(output) > 0

    # Complete input as context variable and print
    context_vars = sk.ContextVariables(simple_input)
    summary = await kernel.run_async(tldr_function, input_vars=context_vars)

    output = str(summary).strip()
    print(f"Completion using context variables: '{output}'")
    assert len(output) > 0

    # Complete input context and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    summary = await kernel.run_async(tldr_function, input_context=context)

    output = str(summary).strip()
    print(f"Completion using input context: '{output}'")
    assert len(output) > 0

    # Complete input context with additional variables and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    context_vars = sk.ContextVariables("running and")
    summary = await kernel.run_async(
        tldr_function, input_context=context, input_vars=context_vars
    )

    output = str(summary).strip()
    print(f"Completion using context and additional variables: '{output}'")
    assert len(output) > 0

    # Complete input context with additional input string and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    summary = await kernel.run_async(
        tldr_function, input_context=context, input_str="running and"
    )

    output = str(summary).strip()
    print(f"Completion using context and additional string: '{output}'")
    assert len(output) > 0

    # Complete input context with additional variables and string and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    context_vars = sk.ContextVariables(variables={"input2": "running and"})
    summary = await kernel.run_async(
        tldr_function,
        input_context=context,
        input_vars=context_vars,
        input_str="new text",
    )

    output = str(summary).strip()
    print(
        f"Completion using context, additional variables, and additional string: '{output}'"
    )
    assert len(output) > 0
