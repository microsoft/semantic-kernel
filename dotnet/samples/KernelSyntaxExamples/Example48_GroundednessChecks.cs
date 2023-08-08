// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Skills.Core;
using RepoUtils;

// ReSharper disable CommentTypo
// ReSharper disable once InconsistentNaming
internal static class Example48_GroundednessChecks
{
    private static string s_groundingText = @"""I am by birth a Genevese, and my family is one of the most distinguished of that republic.
My ancestors had been for many years counsellors and syndics, and my father had filled several public situations
with honour and reputation.He was respected by all who knew him for his integrity and indefatigable attention
to public business.He passed his younger days perpetually occupied by the affairs of his country; a variety
of circumstances had prevented his marrying early, nor was it until the decline of life that he became a husband
and the father of a family.

As the circumstances of his marriage illustrate his character, I cannot refrain from relating them.One of his
most intimate friends was a merchant who, from a flourishing state, fell, through numerous mischances, into poverty.
This man, whose name was Beaufort, was of a proud and unbending disposition and could not bear to live in poverty
and oblivion in the same country where he had formerly been distinguished for his rank and magnificence. Having
paid his debts, therefore, in the most honourable manner, he retreated with his daughter to the town of Lucerne,
where he lived unknown and in wretchedness.My father loved Beaufort with the truest friendship and was deeply
grieved by his retreat in these unfortunate circumstances.He bitterly deplored the false pride which led his friend
to a conduct so little worthy of the affection that united them.He lost no time in endeavouring to seek him out,
with the hope of persuading him to begin the world again through his credit and assistance.

Beaufort had taken effectual measures to conceal himself, and it was ten months before my father discovered his
abode.Overjoyed at this discovery, he hastened to the house, which was situated in a mean street near the Reuss.
But when he entered, misery and despair alone welcomed him. Beaufort had saved but a very small sum of money from
the wreck of his fortunes, but it was sufficient to provide him with sustenance for some months, and in the meantime
he hoped to procure some respectable employment in a merchant's house. The interval was, consequently, spent in
inaction; his grief only became more deep and rankling when he had leisure for reflection, and at length it took
so fast hold of his mind that at the end of three months he lay on a bed of sickness, incapable of any exertion.

His daughter attended him with the greatest tenderness, but she saw with despair that their little fund was
rapidly decreasing and that there was no other prospect of support.But Caroline Beaufort possessed a mind of an
uncommon mould, and her courage rose to support her in her adversity. She procured plain work; she plaited straw
and by various means contrived to earn a pittance scarcely sufficient to support life.

Several months passed in this manner.Her father grew worse; her time was more entirely occupied in attending him;
    her means of subsistence decreased; and in the tenth month her father died in her arms, leaving her an orphan and
a beggar.This last blow overcame her, and she knelt by Beaufort's coffin weeping bitterly, when my father entered
the chamber. He came like a protecting spirit to the poor girl, who committed herself to his care; and after the
interment of his friend he conducted her to Geneva and placed her under the protection of a relation.Two years
after this event Caroline became his wife.""";

    public static async Task RunAsync()
    {
        await GroundednessCheckingSkill();
        await PlanningWithGroundedness();
    }

    public static async Task GroundednessCheckingSkill()
    {
        Console.WriteLine("======== Groundedness Checks ========");
        var kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Logger)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        string folder = RepoFiles.SampleSkillsPath();
        var functions = kernel.ImportSemanticSkillFromDirectory(folder,
            "SummarizePlugin",
            "GroundingPlugin");

        var create_summary = functions["Summarize"];
        var entityExtraction = functions["ExtractEntities"];
        var reference_check = functions["ReferenceCheckEntities"];
        var entity_excision = functions["ExciseEntities"];

        var summaryText = @"
My father, a respected resident of Milan, was a close friend of a merchant named Beaufort who, after a series of
misfortunes, moved to Zurich in poverty. My father was upset by his friend's troubles and sought him out,
finding him in a mean street. Beaufort had saved a small sum of money, but it was not enough to support him and
his daughter, Mary. Mary procured work to eek out a living, but after ten months her father died, leaving
her a beggar. My father came to her aid and two years later they married.
";

        var context = kernel.CreateNewContext();
        context.Variables.Update(summaryText);
        context.Variables.Set("topic", "people and places");
        context.Variables.Set("example_entities", "John, Jane, mother, brother, Paris, Rome");

        var extractionResult = (await entityExtraction.InvokeAsync(context)).Result;

        Console.WriteLine("======== Extract Entities ========");
        Console.WriteLine(extractionResult);

        context.Variables.Update(extractionResult);
        context.Variables.Set("reference_context", s_groundingText);

        var groundingResult = (await reference_check.InvokeAsync(context)).Result;

        Console.WriteLine("======== Reference Check ========");
        Console.WriteLine(groundingResult);

        context.Variables.Update(summaryText);
        context.Variables.Set("ungrounded_entities", groundingResult);
        var excisionResult = await entity_excision.InvokeAsync(context);

        Console.WriteLine("======== Excise Entities ========");
        Console.WriteLine(excisionResult.Result);
    }

    public static async Task PlanningWithGroundedness()
    {
        var targetTopic = "people and places";
        var samples = "John, Jane, mother, brother, Paris, Rome";
        var ask = @$"Make a summary of input text. Then make a list of entities
related to {targetTopic} (such as {samples}) which are present in the summary.
Take this list of entities, and from it make another list of those which are not
grounded in the original input text. Finally, rewrite your summary to remove the entities
which are not grounded in the original.
";

        Console.WriteLine("======== Planning - Groundedness Checks ========");

        var kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Logger)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        string folder = RepoFiles.SampleSkillsPath();
        var functions = kernel.ImportSemanticSkillFromDirectory(folder,
            "SummarizePlugin",
            "GroundingPlugin");

        kernel.ImportSkill(new TextSkill());

        var planner = new SequentialPlanner(kernel);
        var plan = await planner.CreatePlanAsync(ask);
        Console.WriteLine(plan.ToPlanWithGoalString());

        var results = await plan.InvokeAsync(s_groundingText);
        Console.WriteLine(results.Result);
    }
}

/* Example Output:
======== Groundedness Checks ========
======== Extract Entities ========
<entities>
- Milan
- Beaufort
- Zurich
- Mary
</entities>
======== Reference Check ========
<ungrounded_entities>
- Milan
- Zurich
- Mary
</ungrounded_entities>
======== Excise Entities ========
My father, a respected resident of a city, was a close friend of a merchant named Beaufort who, after a series of
misfortunes, moved to another city in poverty. My father was upset by his friend's troubles and sought him out,
finding him in a mean street. Beaufort had saved a small sum of money, but it was not enough to support him and
his daughter. The daughter procured work to eek out a living, but after ten months her father died, leaving
her a beggar. My father came to her aid and two years later they married.
======== Planning - Groundedness Checks ========
Goal: Make a summary of input text. Then make a list of entities
related to people and places (such as John, Jane, mother, brother, Paris, Rome) which are present in the summary.
Take this list of entities, and from it make another list of those which are not
grounded in the original input text. Finally, rewrite your summary to remove the entities
which are not grounded in the original.




Steps:
  - _GLOBAL_FUNCTIONS_.Echo INPUT='' => ORIGINAL_TEXT
  - SummarizePlugin.Summarize INPUT='' => RESULT__SUMMARY
  - GroundingPlugin.ExtractEntities example_entities='John;Jane;mother;brother;Paris;Rome' topic='people and places' INPUT='$RESULT__SUMMARY' => ENTITIES
  - GroundingPlugin.ReferenceCheckEntities reference_context='$ORIGINAL_TEXT' INPUT='$ENTITIES' => RESULT__UNGROUND_ENTITIES
  - GroundingPlugin.ExciseEntities ungrounded_entities='$RESULT__UNGROUND_ENTITIES' INPUT='$RESULT__SUMMARY' => RESULT__FINAL_SUMMARY
A possible summary is:



The narrator's father, a respected Genevese politician, befriended Beaufort, a merchant who fell into poverty and hid in Lucerne. After a long search, he found him dying and his daughter Caroline working hard to survive. He took pity on Caroline, buried Beaufort, and married her two years later.
<ungrounded_entities>
- narrator
</ungrounded_entities>
A possible summary is:



The father of the story's main character, a respected Genevese politician, befriended Beaufort, a merchant who fell into poverty and hid in Lucerne. After a long search, he found him dying and his daughter Caroline working hard to survive. He took pity on Caroline, buried Beaufort, and married her two years later.
== DONE ==
*/
