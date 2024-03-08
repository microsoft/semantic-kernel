import asyncio
import logging

import semantic_kernel as sk
from samples.utils import Colors
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatCompletion,
)


def get_grounding_text():
    return """I am by birth a Genevese, and my family is one of the most distinguished of that republic.
My ancestors had been for many years counsellors and syndics, and my father had filled several public situations
with honour and reputation. He was respected by all who knew him for his integrity and indefatigable attention
to public business. He passed his younger days perpetually occupied by the affairs of his country; a variety
of circumstances had prevented his marrying early, nor was it until the decline of life that he became a husband
and the father of a family.

As the circumstances of his marriage illustrate his character, I cannot refrain from relating them. One of his
most intimate friends was a merchant who, from a flourishing state, fell, through numerous mischances, into poverty.
This man, whose name was Beaufort, was of a proud and unbending disposition and could not bear to live in poverty
and oblivion in the same country where he had formerly been distinguished for his rank and magnificence. Having
paid his debts, therefore, in the most honourable manner, he retreated with his daughter to the town of Lucerne,
where he lived unknown and in wretchedness. My father loved Beaufort with the truest friendship and was deeply
grieved by his retreat in these unfortunate circumstances. He bitterly deplored the false pride which led his friend
to a conduct so little worthy of the affection that united them. He lost no time in endeavouring to seek him out,
with the hope of persuading him to begin the world again through his credit and assistance.

Beaufort had taken effectual measures to conceal himself, and it was ten months before my father discovered his
abode. Overjoyed at this discovery, he hastened to the house, which was situated in a mean street near the Reuss.
But when he entered, misery and despair alone welcomed him. Beaufort had saved but a very small sum of money from
the wreck of his fortunes, but it was sufficient to provide him with sustenance for some months, and in the meantime
he hoped to procure some respectable employment in a merchant's house. The interval was, consequently, spent in
inaction; his grief only became more deep and rankling when he had leisure for reflection, and at length it took
so fast hold of his mind that at the end of three months he lay on a bed of sickness, incapable of any exertion.

His daughter attended him with the greatest tenderness, but she saw with despair that their little fund was
rapidly decreasing and that there was no other prospect of support. But Caroline Beaufort possessed a mind of an
uncommon mould, and her courage rose to support her in her adversity. She procured plain work; she plaited straw
and by various means contrived to earn a pittance scarcely sufficient to support life.

Several months passed in this manner. Her father grew worse; her time was more entirely occupied in attending him;
her means of subsistence decreased; and in the tenth month her father died in her arms, leaving her an orphan and
a beggar. This last blow overcame her, and she knelt by Beaufort's coffin weeping bitterly, when my father entered
the chamber. He came like a protecting spirit to the poor girl, who committed herself to his care; and after the
interment of his friend he conducted her to Geneva and placed her under the protection of a relation. Two years
after this event Caroline became his wife."""


def setup(use_azure: bool = False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    kernel = sk.Kernel(log=logger)

    useAzureOpenAI = use_azure

    # Configure AI service used by the kernel
    if useAzureOpenAI:
        deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
        service_id = ("chat_completion",)
        kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key,
                api_version="2023-12-01-preview",
                log=logger,
            ),
        )
    else:
        api_key, org_id = sk.openai_settings_from_dot_env()
        service_id = "chat-gpt"
        kernel.add_service(
            OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id),
        )

    # note: using plugins from the samples folder
    plugins_directory = "../samples/plugins/"

    grounding_semantic_functions = kernel.import_plugin_from_prompt_directory(
        service_id, plugins_directory, "GroundingPlugin"
    )

    return kernel, grounding_semantic_functions


def get_summary_text():
    summary_text = """My father, a respected resident of Milan, was a close friend of a merchant named Beaufort who, after a series of misfortunes, moved to Zurich in poverty. My father was upset by his friend's troubles and sought him out, finding him in a mean street. Beaufort had saved a small sum of money, but it was not enough to support him and his daughter, Mary. Mary procured work to eek out a living, but after ten months her father died, leaving her a beggar. My father came to her aid and two years later they married when they visited Rome."""  # noqa: E501

    summary_text = summary_text.replace("\n", " ").replace("  ", " ")
    return summary_text


async def run_entity_extraction(kernel, semantic_functions, summary_text):
    context = kernel.create_new_context()
    context["topic"] = "people and places"
    context["example_entities"] = "John, Jane, mother, brother, Paris, Rome"

    extraction_result = semantic_functions["ExtractEntities"](summary_text, context=context)

    return extraction_result, context


async def run_reference_check(semantic_functions, extraction_result, context):
    context["reference_context"] = get_grounding_text()

    grounding_result = semantic_functions["ReferenceCheckEntities"](extraction_result.result, context=context)
    context["ungrounded_entities"] = grounding_result.result
    return grounding_result, context


async def run_entity_excision(semantic_functions, summary_text, context):
    excision_result = semantic_functions["ExciseEntities"](summary_text, context=context)
    return excision_result, context


async def run_grounding(use_azure: bool = False):
    kernel, semantic_functions = setup(use_azure)
    print(f"\n{Colors.CBOLD}Groundingsness Checking Plugins\n{Colors.CEND}")
    print(f"\n{ '-'*80 }\n")
    print(
        f"""{Colors.CGREEN}A well-known problem with large language models (LLMs) is that they make things up. These are sometimes called 'hallucinations' but a safer (and less anthropomorphic) term is 'ungrounded addition' - something in the text which cannot be firmly established. When attempting to establish whether or not something in an LLM response is 'true' we can either check for it in the supplied prompt (this is called 'narrow grounding') or use our general knowledge ('broad grounding'). Note that narrow grounding can lead to things being classified as 'true, but ungrounded.' For example "I live in Switzerland" is **not** _narrowly_ grounded in "I live in Geneva" even though it must be true (it **is** _broadly_ grounded).  # noqa: E501

In this sample we run a simple grounding pipeline, to see if a summary text has any ungrounded additions as compared to the original, and use this information to improve the summary text. This can be done in three stages:  # noqa: E501

1. Make a list of the entities in the summary text
1. Check to see if these entities appear in the original (grounding) text
1. Remove the ungrounded entities from the summary text

What is an 'entity' in this context? In its simplest form, it's a named object such as a person or place (so 'Dean' or 'Seattle'). However, the idea could be a _claim_ which relates concepts (such as 'Dean lives near Seattle'). In this sample, we will keep to the simpler case of named objects."""  # noqa: E501
    )

    print(f"\nThe grounding text: \n{Colors.CGREY}{get_grounding_text()}{Colors.CEND}")

    print(f"\n{ '-'*80 }\n")
    summary_text = get_summary_text()
    print(f"Summary text: \n{Colors.CBLUE}{summary_text}{Colors.CEND}")
    print(f"\n{ '-'*80 }\n")
    print(
        f"""{Colors.CGREEN}Some things to note:

- The implied residence of Geneva has been changed to Milan
- Lucerne has been changed to Zurich
- Caroline has been renamed as Mary
- A reference to Rome has been added


The grounding plugin has three stages:

1. Extract entities from a summary text
2. Perform a reference check against the grounding text
3. Excise any entities which failed the reference check from the summary

Now, let us start calling individual semantic functions.{Colors.CEND}"""
    )
    print(f"\n{ '-'*80 }\n")
    print(
        f"{Colors.CGREEN}First we run the extraction function on the summary, this results in all the extracted entities.{Colors.CEND}"  # noqa: E501
    )
    extraction_result, context = await run_entity_extraction(kernel, semantic_functions, summary_text)
    print(f"Extraction result: \n{Colors.CBLUE}{extraction_result.result}{Colors.CEND}")
    print(f"\n{ '-'*80 }\n")
    print(
        f"{Colors.CGREEN}Next we run the reference check function on the summary, this loads the grounding text as part of it in order to know the 'truth'. This returns a list of ungrounded entities.{Colors.CEND}"  # noqa: E501
    )
    grounding_result, context = await run_reference_check(semantic_functions, extraction_result, context)
    print(f"Grounding result: \n{Colors.CBLUE}{grounding_result.result}{Colors.CEND}")
    print(f"\n{ '-'*80 }\n")
    print(
        f"{Colors.CGREEN}Finally we run the excision function on the summary, this removes the ungrounded entities from the summary.{Colors.CEND}"  # noqa: E501
    )
    excision_result, context = await run_entity_excision(semantic_functions, summary_text, context)
    print(f"The final summary text: \n{Colors.CBLUE}{excision_result.result}{Colors.CEND}")
    print(f"\n{ '-'*80 }\n")
    print(f"{Colors.CBOLD}Finished!{Colors.CEND}")


if __name__ == "__main__":
    asyncio.run(run_grounding(use_azure=True))
