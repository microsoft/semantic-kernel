from unittest.mock import Mock
from pytest import fixture, mark
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition.read_only_skill_collection import (
    ReadOnlySkillCollection,
)
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.guidance_prompt_template_engine import (
    GuidanceTemplateEngine,
)
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine
from semantic_kernel.utils.null_logger import NullLogger


@fixture
def target():
    return GuidanceTemplateEngine()


@fixture
def variables():
    return ContextVariables("X")


@fixture
def skills():
    return Mock(spec=ReadOnlySkillCollection)


@fixture
def context(variables, skills):
    return SKContext(variables, NullMemory(), skills, NullLogger())


def test_it_renders_variables(
    target: PromptTemplateEngine, variables: ContextVariables
):
    template = (
        "{$x11} This {$a} is {{$x11}}"
        "with {{%guidance}} type {{%variables}}"
        "{{code}} and {{gen block}}"
    )

    blocks = target.extract_blocks(template)
    updated_blocks = target.render_variables(blocks, variables)

    assert len(blocks) == 9
    assert len(updated_blocks) == 9

    assert blocks[1].content == "$x11"
    assert updated_blocks[1].content == ""
    assert blocks[1].type == BlockTypes.VARIABLE
    assert updated_blocks[1].type == BlockTypes.TEXT

    variables.set("x11", "x11 value")
    updated_blocks = target.render_variables(blocks, variables)
    assert updated_blocks[1].content == "x11 value"

    assert blocks[3].content == "%guidance"
    assert updated_blocks[3].content == "%guidance"
    assert blocks[3].type == BlockTypes.GUIDANCE
    assert updated_blocks[3].type == BlockTypes.GUIDANCE

    assert blocks[5].content == "%variables"
    assert updated_blocks[5].content == "%variables"
    assert blocks[5].type == BlockTypes.GUIDANCE
    assert updated_blocks[5].type == BlockTypes.GUIDANCE

    assert blocks[6].content == "code"
    assert updated_blocks[6].content == "code"
    assert blocks[6].type == BlockTypes.CODE
    assert updated_blocks[6].type == BlockTypes.CODE

    assert blocks[8].content == "gen block"
    assert updated_blocks[8].content == "gen block"
    assert blocks[8].type == BlockTypes.GUIDANCE
    assert updated_blocks[8].type == BlockTypes.GUIDANCE


@mark.asyncio
async def test_guidance_variable_char(
    target: PromptTemplateEngine,
    variables: ContextVariables,
    skills: Mock,
    context: SKContext,
):
    template = "This is a test with {{%guidance}} type {{%variables}}"

    result = await target.render_async(template, context)

    assert result == "This is a test with {{guidance}} type {{variables}}"


@mark.asyncio
async def test_guidance_handlebar_char(
    target: PromptTemplateEngine,
    variables: ContextVariables,
    skills: Mock,
    context: SKContext,
):
    template = """The following is a character profile for an RPG game in JSON format.
    ```json
{
    "description": "{{%description}}",
    "name": "{{gen 'name'}}",
    "age": {{gen 'age' stop=','}},
    "armor": "{{#select 'armor'}}leather{{or}}chainmail{{or}}plate{{/select}}",
    "weapon": "{{select 'weapon' options=valid_weapons}}",
    "class": "{{gen 'class'}}",
    "biography": "{{gen 'biography'}}",
    "mantra": "{{gen 'mantra'}}",
    "strength": {{gen 'strength' stop=','}},
    "items": [{{#geneach 'items' num_iterations=3}}
        "{{gen 'this'}}",{{/geneach}}
    ]
}```"""

    result = await target.render_async(template, context)

    assert (
        result
        == """The following is a character profile for an RPG game in JSON format.
    ```json
{
    "description": "{{description}}",
    "name": "{{gen 'name'}}",
    "age": {{gen 'age' stop=','}},
    "armor": "{{#select 'armor'}}leather{{or}}chainmail{{or}}plate{{/select}}",
    "weapon": "{{select 'weapon' options=valid_weapons}}",
    "class": "{{gen 'class'}}",
    "biography": "{{gen 'biography'}}",
    "mantra": "{{gen 'mantra'}}",
    "strength": {{gen 'strength' stop=','}},
    "items": [{{#geneach 'items' num_iterations=3}}
        "{{gen 'this'}}",{{/geneach}}
    ]
}```"""
    )
