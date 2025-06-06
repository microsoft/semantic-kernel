﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using xRetry;

namespace Plugins;

public class GroundednessChecks(ITestOutputHelper output) : BaseTest(output)
{
    [RetryFact(typeof(HttpOperationException))]
    public async Task GroundednessCheckingAsync()
    {
        Console.WriteLine("\n======== Groundedness Checks ========");
        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();

        string folder = RepoFiles.SamplePluginsPath();
        var summarizePlugin = kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "SummarizePlugin"));
        var groundingPlugin = kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "GroundingPlugin"));

        var create_summary = summarizePlugin["Summarize"];
        var entityExtraction = groundingPlugin["ExtractEntities"];
        var reference_check = groundingPlugin["ReferenceCheckEntities"];
        var entity_excision = groundingPlugin["ExciseEntities"];

        var summaryText = @"
My father, a respected resident of Milan, was a close friend of a merchant named Beaufort who, after a series of
misfortunes, moved to Zurich in poverty. My father was upset by his friend's troubles and sought him out,
finding him in a mean street. Beaufort had saved a small sum of money, but it was not enough to support him and
his daughter, Mary. Mary procured work to eek out a living, but after ten months her father died, leaving
her a beggar. My father came to her aid and two years later they married.
";

        KernelArguments variables = new()
        {
            ["input"] = summaryText,
            ["topic"] = "people and places",
            ["example_entities"] = "John, Jane, mother, brother, Paris, Rome"
        };

        var extractionResult = (await kernel.InvokeAsync(entityExtraction, variables)).ToString();

        Console.WriteLine("======== Extract Entities ========");
        Console.WriteLine(extractionResult);

        variables["input"] = extractionResult;
        variables["reference_context"] = GroundingText;

        var groundingResult = (await kernel.InvokeAsync(reference_check, variables)).ToString();

        Console.WriteLine("\n======== Reference Check ========");
        Console.WriteLine(groundingResult);

        variables["input"] = summaryText;
        variables["ungrounded_entities"] = groundingResult;
        var excisionResult = await kernel.InvokeAsync(entity_excision, variables);

        Console.WriteLine("\n======== Excise Entities ========");
        Console.WriteLine(excisionResult.GetValue<string>());
    }

    private const string GroundingText = """
        "I am by birth a Genevese, and my family is one of the most distinguished of that republic.
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
        after this event Caroline became his wife."
        """;
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
*/
