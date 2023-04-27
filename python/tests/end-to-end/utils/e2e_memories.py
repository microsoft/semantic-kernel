import semantic_kernel as sk


async def simple_memory_test(kernel: sk.Kernel):
    # Add some documents to the semantic memory
    await kernel.memory.save_information_async(
        "test", id="info1", text="Sharks are fish."
    )
    await kernel.memory.save_information_async(
        "test", id="info2", text="Whales are mammals."
    )
    await kernel.memory.save_information_async(
        "test", id="info3", text="Penguins are birds."
    )
    await kernel.memory.save_information_async(
        "test", id="info4", text="Dolphins are mammals."
    )
    await kernel.memory.save_information_async(
        "test", id="info5", text="Flies are insects."
    )

    # Search for documents
    result = await kernel.memory.search_async(
        "test", "What are mammals?", limit=2, min_relevance_score=0.0
    )
    print(f"#1 Answer: {result[0].text}\n")
    print(f"#2 Answer: {result[1].text}\n")
    assert "mammals." in result[0].text
    assert "mammals." in result[1].text

    result = await kernel.memory.search_async(
        "test", "What are fish?", limit=1, min_relevance_score=0.0
    )
    print(f"#1 Answer: {result[0].text}\n")
    assert result[0].text == "Sharks are fish."

    result = await kernel.memory.search_async(
        "test", "What are insects?", limit=1, min_relevance_score=0.0
    )
    print(f"#1 Answer: {result[0].text}\n")
    assert result[0].text == "Flies are insects."

    result = await kernel.memory.search_async(
        "test", "What are birds?", limit=1, min_relevance_score=0.0
    )
    print(f"#1 Answer: {result[0].text}\n")
    assert result[0].text == "Penguins are birds."
