// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.Sequential;
using Microsoft.SemanticKernel.Planning.Structured;
using Microsoft.SemanticKernel.Planning.Structured.Sequential;
using Microsoft.SemanticKernel.Plugins.Core;
using RepoUtils;
using Skills;


// ReSharper disable CommentTypo
// ReSharper disable once InconsistentNaming
internal static class Example12_SequentialPlanner
{
    public static async Task RunAsync()
    {
        await PoetrySamplesAsync();
        await EmailSamplesWithRecallAsync();
        await BookSamplesAsync();
        await MemorySampleAsync();
        await PlanNotPossibleSampleAsync();
    }


    private static async Task PlanNotPossibleSampleAsync()
    {
        Console.WriteLine("======== Sequential Planner - Plan Not Possible ========");
        var kernel = InitializeKernelAndPlanner(out var planner);

        // Load additional skills to enable planner but not enough for the given goal.
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticPluginFromDirectory(folder, "SummarizeSkill");

        try
        {
            await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");
        }
        catch (SKException e)
        {
            Console.WriteLine(e.Message);
            // Create plan error: Not possible to create plan for goal with available functions.
            // Goal:Write a poem about John Doe, then translate it into Italian.
            // Functions:
            // SummarizeSkill.MakeAbstractReadable:
            //   description: Given a scientific white paper abstract, rewrite it to make it more readable
            //   inputs:
            //     - input:

            // SummarizeSkill.Notegen:
            //   description: Automatically generate compact notes for any text or text document.
            //   inputs:
            //     - input:

            // SummarizeSkill.Summarize:
            //   description: Summarize given text or any text document
            //   inputs:
            //     - input: Text to summarize

            // SummarizeSkill.Topics:
            //   description: Analyze given text or document and extract key topics worth remembering
            //   inputs:
            //     - input:
        }
    }


    private static async Task PoetrySamplesAsync(bool useStructuredPlanner = false)
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Poetry Plan ========");
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticPluginFromDirectory(folder,
           "SummarizeSkill",
           "WriterSkill");

        Plan plan = null;

        if (!useStructuredPlanner)
        {
            var planner = new SequentialPlanner(kernel);
            plan = await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");
        }

        else
        {
            var planner = new StructuredSequentialPlanner(kernel);
            plan = await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");
        }

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.ToPlanWithGoalString());

        var result = await ExecutePlanAsync(kernel, plan);

        Console.WriteLine("Result:");
        Console.WriteLine(result.State.ToString());

        /*
        Observed Output:
        Sequential planner output:
          Original plan:
            Goal: Write a poem about John Doe, then translate it into Italian.

            Steps:
            - WriterSkill.ShortPoem INPUT='John Doe is a friendly guy who likes to help others and enjoys reading books.' =>
            - WriterSkill.Translate language='Italian' INPUT='' =>

            Tokens:
            - CreatePlan: Total Tokens: 1549 Prompt Tokens: 1473 Completion Tokens: 76
            - WriterPoem.ShortPoem: Total Tokens: 110 Prompt Tokens: 50 Completion Tokens: 60
            - WriterSkill.Translate: Total Tokens: 153 Prompt Tokens: 96 Completion Tokens: 57
            - Totals:
                Total Tokens: 1812
                Prompt Tokens: 1619
                Completion Tokens: 193

            Result:
            Step 1: Write Poem
                There once was a fellow named John Doe,
                Whose life was as fast as a robo.
                He ran here and there,
                With hardly a care,
                Till he tripped on a pebble and yelled, "Oh no!"

                He fell in a puddle, quite deep,
                His clothes were

            Step 2: Translate to Italian
                Once upon a time, there was a man named John Doe,
                Whose life was as fast as a robot.
                He ran here and there,
                Without much worry,
                Until he tripped on a pebble and yelled, "Oh no!"

                He fell into a deep puddle,
                His clothes were...

        Structured sequential planner output:
             Original plan:
                 Goal: Write a poem about John Doe, then translate it into Italian.

                Steps:
                - WriterSkill.Brainstorm INPUT = 'John Doe' => BRAINSTORM_IDEAS
                - WriterSkill.ShortPoem INPUT = '$BRAINSTORM_IDEAS' => POEM
                - WriterSkill.Translate INPUT = '$POEM' language = 'Italian' => TRANSLATED_POEM

               Tokens:
               - CreatePlan: Total Tokens: 1194 Prompt Tokens: 938 Completion Tokens: 256
               - WriterSkill.BrainStorm: Total Tokens: 203 Prompt Tokens: 72 Completion Tokens: 131
               - WriterPoem.ShortPoem: Total Tokens: 237 Prompt Tokens: 177 Completion Tokens: 60
               - WriterSkill.Translate: Total Tokens: 179 Prompt Tokens: 96 Completion Tokens: 83
               - Totals:
                    Total Tokens: 1813
                    Prompt Tokens: 1283
                    Completion Tokens: 530

            Result:
            Step 1 Brainstorm
                1.John Doe's childhood experiences and how they shaped his character.
                2.The key accomplishments of John Doe in his professional career.
                3.The challenges faced by John Doe and how he overcame them.
                4.John Doe's influential role models and how they influenced his life.
                5.The hobbies and interests of John Doe outside his professional life.
                6.The unique traits and characteristics that set John Doe apart.
                7.The future aspirations and goals of John Doe.
                8.John Doe's contributions to his local community.
                9.The lessons learned by John Doe throughout his journey.
                10.The legacy that John Doe wants to leave behind.

            Step 2 Write poem
               1. John Doe, as a child, was quite a sight,
               Loved mud pies more than a kite.
               Now he's a chef, with a flair,
               His past, in his dishes, he does share.

               2. John climbed the ladder, oh so high,
               His success

            Step 3 Translate to Italian:
               1. John Doe, da bambino, era proprio una vista,
               Amava le torte di fango più di un aquilone.
               Ora è uno chef, con un tocco,
               Il suo passato, nei suoi piatti, condivide.

               2. John ha scalato la scala, oh così in alto,
               Il suo successo
        */

    }


    private static async Task EmailSamplesWithRecallAsync(bool useStructuredPlanner = false)
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Email Plan ========");
        var kernel = InitializeKernelAndPlanner(out var planner, 512);
        kernel.ImportPlugin(new EmailSkill(), "email");

        // Load additional skills to enable planner to do non-trivial asks.
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticPluginFromDirectory(folder,
           "SummarizeSkill",
           "WriterSkill");

        var plan = await planner.CreatePlanAsync("Summarize an input, translate to french, and e-mail to John Doe");

        // Original plan:
        // Goal: Summarize an input, translate to french, and e-mail to John Doe

        // Steps:
        // - SummarizeSkill.Summarize INPUT='' =>
        // - WriterSkill.Translate language='French' INPUT='' => TRANSLATED_SUMMARY
        // - email.GetEmailAddress INPUT='John Doe' => EMAIL_ADDRESS
        // - email.SendEmail INPUT='$TRANSLATED_SUMMARY' email_address='$EMAIL_ADDRESS' =>

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.ToPlanWithGoalString());

        // Serialize plan before execution for saving to memory on success.
        var originalPlan = plan.ToJson();

        var input =
            "Once upon a time, in a faraway kingdom, there lived a kind and just king named Arjun. " +
            "He ruled over his kingdom with fairness and compassion, earning him the love and admiration of his people. " +
            "However, the kingdom was plagued by a terrible dragon that lived in the nearby mountains and terrorized the nearby villages, " +
            "burning their crops and homes. The king had tried everything to defeat the dragon, but to no avail. " +
            "One day, a young woman named Mira approached the king and offered to help defeat the dragon. She was a skilled archer " +
            "and claimed that she had a plan to defeat the dragon once and for all. The king was skeptical, but desperate for a solution, " +
            "so he agreed to let her try. Mira set out for the dragon's lair and, with the help of her trusty bow and arrow, " +
            "she was able to strike the dragon with a single shot through its heart, killing it instantly. The people rejoiced " +
            "and the kingdom was at peace once again. The king was so grateful to Mira that he asked her to marry him and she agreed. " +
            "They ruled the kingdom together, ruling with fairness and compassion, just as Arjun had done before. They lived " +
            "happily ever after, with the people of the kingdom remembering Mira as the brave young woman who saved them from the dragon.";

        var originalPlan = string.Empty;
        Plan plan = null;

        if (useStructuredPlanner)
        {
            kernel = InitializeKernelAndStructuredPlanner(out var structuredSequentialPlanner, 512);
            kernel.ImportSkill(new EmailSkill(), "email");

            // Load additional skills to enable planner to do non-trivial asks.
            var folder = RepoFiles.SampleSkillsPath();
            kernel.ImportSemanticSkillFromDirectory(folder,
                "SummarizeSkill",
                "WriterSkill");

            plan = await structuredSequentialPlanner.CreatePlanAsync("Summarize an input, translate to french, and e-mail to John Doe");

            Console.WriteLine("Original plan:");
            Console.WriteLine(plan.ToPlanWithGoalString());

            // Serialize plan before execution for saving to memory on success.
            originalPlan = plan.ToJson();

            Console.WriteLine("======== Sequential Planner - Find and Execute Saved Plan ========");

        }
        else
        {
            kernel = InitializeKernelAndPlanner(out var sequentialPlanner, 512);
            kernel.ImportSkill(new EmailSkill(), "email");

            // Load additional skills to enable planner to do non-trivial asks.
            var folder = RepoFiles.SampleSkillsPath();
            kernel.ImportSemanticSkillFromDirectory(folder,
                "SummarizeSkill",
                "WriterSkill");

            plan = await sequentialPlanner.CreatePlanAsync("Summarize an input, translate to french, and e-mail to John Doe");

            Console.WriteLine("Original plan:");
            Console.WriteLine(plan.ToPlanWithGoalString());

            // Serialize plan before execution for saving to memory on success.
            originalPlan = plan.ToJson();

        }

        await ExecutePlanAsync(kernel, plan, input, 5);

        var semanticMemory = GetMemory();
        await semanticMemory.SaveInformationAsync(
            "plans",
            id: Guid.NewGuid().ToString(),
            text: plan.Description, // This is the goal used to create the plan
            description: originalPlan);

        var goal = "Write summary in french and e-mail John Doe";

        Console.WriteLine($"Goal: {goal}");
        Console.WriteLine("Searching for saved plan...");

        Plan? restoredPlan = null;
        IAsyncEnumerable<MemoryQueryResult> memories = semanticMemory.SearchAsync("plans", goal, 1, 0.5);

        await foreach (var memory in memories)
        {
            Console.WriteLine($"Restored plan (relevance={memory.Relevance}):");

            // Deseriliaze the plan from the description
            restoredPlan = Plan.FromJson(memory.Metadata.Description, kernel.Functions);

            Console.WriteLine(restoredPlan.ToPlanWithGoalString());
            Console.WriteLine();

            break;
        }

        if (restoredPlan is not null)
        {
            var newInput =
                "Far in the future, on a planet lightyears away, 15 year old Remy lives a normal life. He goes to school, " +
                "hangs out with his friends, and tries to avoid trouble. But when he stumbles across a secret that threatens to destroy " +
                "everything he knows, he's forced to go on the run. With the help of a mysterious girl named Eve, he must evade the ruthless " +
                "agents of the Galactic Federation, and uncover the truth about his past. But the more he learns, the more he realizes that " +
                "he's not just an ordinary boy.";

            var result = await kernel.RunAsync(restoredPlan, new(newInput));

            Console.WriteLine("Result:");
            Console.WriteLine(result.Result);
        }

        /*
          Observed Output:
            Sequential planner output:
                Original plan:
                - Goal: Summarize an input, translate to french, and e-mail to John Doe

               Steps:
               - SummarizeSkill.Summarize INPUT='$INPUT' => SUMMARY
               - WriterSkill.Translate language='fr' INPUT='$SUMMARY' => TRANSLATED_SUMMARY
               - email.GetEmailAddress INPUT='John Doe' => EMAIL_ADDRESS
               - email.SendEmail INPUT='$TRANSLATED_SUMMARY' email_address='$EMAIL_ADDRESS'

               Tokens:
                - CreatePlan: Total Tokens: 1700 Prompt Tokens: 1560 Completion Tokens: 140
                - SummarizeSkill.Summarize: Total Tokens: 511 Prompt Tokens: 385 Completion Tokens: 126
                - WriterSkill.Translate: Total Tokens: 364 Prompt Tokens: 161 Completion Tokens: 203
                - email.GetEmailAddress: Total Tokens: 305 Prompt Tokens: 230 Completion Tokens: 75
                - email.SendEmail: Total Tokens: 228 Prompt Tokens: 110 Completion Tokens: 118
                - Totals:
                    Total Tokens: 3108
                    Prompt Tokens: 2446
                    Completion Tokens: 662

                Result:
                Step 1: Summarize
                - In a distant kingdom, a benevolent King Arjun struggled to protect his people from a destructive dragon.
                Despite his efforts, he couldn't defeat the beast. A young archer, Mira, offered her help, claiming she had a plan to kill the dragon.
                Skeptical but desperate, Arjun agreed. Mira successfully killed the dragon with a single arrow, bringing peace back to the kingdom.
                Grateful, Arjun proposed to Mira, and they ruled the kingdom together, continuing Arjun's legacy of fairness and compassion.
                Their story ended happily, with Mira remembered as the heroine who saved the kingdom.

                Step 2: Translate
                - Dans un royaume lointain, un roi bienveillant nommé Arjun luttait pour protéger son peuple d'un dragon destructeur.
                Malgré ses efforts, il ne pouvait pas vaincre la bête. Une jeune archère, Mira, a proposé son aide, affirmant qu'elle avait un plan pour tuer le dragon.
                Sceptique mais désespéré, Arjun a accepté. Mira a réussi à tuer le dragon avec une seule flèche, ramenant la paix dans le royaume.
                Reconnaissant, Arjun a demandé Mira en mariage, et ils ont régné ensemble sur le royaume, perpétuant l'héritage d'équité et de compassion d'Arjun.
                Leur histoire s'est terminée heureusement, avec Mira se souvenant comme l'héroïne qui a sauvé le royaume.

                Step 3: Get email address
                - johndoe1234@example.com

                Step 4: Send email
                - Sent email to: johndoe1234@example.com.
                  Body: Dans un royaume lointain, un roi bienveillant nommé Arjun luttait pour protéger son peuple d'un dragon destructeur. Malgré ses efforts,
                  il ne pouvait pas vaincre la bête. Une jeune archère, Mira, a proposé son aide, affirmant qu'elle avait un plan pour tuer le dragon.
                  Sceptique mais désespéré, Arjun a accepté. Mira a réussi à tuer le dragon avec une seule flèche, ramenant la paix dans le royaume.
                  Reconnaissant, Arjun a demandé Mira en mariage, et ils ont régné ensemble sur le royaume, perpétuant l'héritage d'équité et de
                  compassion d'Arjun. Leur histoire s'est terminée heureusement, avec Mira se souvenant comme l'héroïne qui a sauvé le royaume.

                Execution complete in 31007 ms!

            Structured sequential planner output:
                Original plan:
                - Goal: Summarize an input, translate to french, and e-mail to John Doe

               Steps:
               - SummarizeSkill.Summarize INPUT='$INPUT' => SUMMARIZED_TEXT
               - WriterSkill.Translate INPUT='$SUMMARIZED_TEXT' language='French' => TRANSLATED_TEXT
               - email.GetEmailAddress INPUT='John Doe' => JOHN_DOE_EMAIL
               - email.SendEmail INPUT='$TRANSLATED_TEXT' email_address='$JOHN_DOE_EMAIL'

               Tokens:
                - CreatePlan: Total Tokens: Tokens: 1363 Prompt Tokens: 1032 Completion Tokens: 331
                - SummarizeSkill.Summarize: Total Tokens: 511 Prompt Tokens: 385 Completion Tokens: 126
                - WriterSkill.Translate: Total Tokens: 374 Prompt Tokens: 161 Completion Tokens: 213
                - email.GetEmailAddress: Total Tokens: 305 Prompt Tokens: 230 Completion Tokens: 75
                - email.SendEmail: Total Tokens: 228 Prompt Tokens: 110 Completion Tokens: 118
                - Totals:
                    Total Tokens: 2781
                    Prompt Tokens: 1918
                    Completion Tokens: 863

                Result:
                Step 1: Summarize
                - In a distant kingdom, a benevolent King Arjun struggled to protect his people from a destructive dragon. Despite his efforts, he couldn't defeat the beast.
                A young archer, Mira, offered her help, claiming she had a plan to kill the dragon. Skeptical but desperate, Arjun agreed. Mira successfully killed the dragon
                with a single arrow, bringing peace back to the kingdom. Grateful, Arjun proposed to Mira, and they ruled the kingdom together, continuing Arjun's legacy of
                fairness and compassion. Their story ended happily, with Mira remembered as the heroine who saved the kingdom.

                Step 2: Translate
                - Assurez-vous d'utiliser uniquement le français.

                Dans un royaume lointain, un roi bienveillant nommé Arjun luttait pour protéger son peuple d'un dragon destructeur. Malgré ses efforts, il ne pouvait pas vaincre
                la bête. Une jeune archère, Mira, a proposé son aide, affirmant qu'elle avait un plan pour tuer le dragon. Sceptique mais désespéré, Arjun a accepté. Mira a réussi
                à tuer le dragon avec une seule flèche, ramenant la paix dans le royaume. Reconnaissant, Arjun a demandé Mira en mariage, et ils ont régné ensemble sur le royaume,
                perpétuant l'héritage d'Arjun de justice et de compassion. Leur histoire s'est terminée heureusement, avec Mira se souvenant comme l'héroïne qui a sauvé le royaume.

                Step 3: Get email address
                - johndoe123@example.com

                Step 4: Send email
                - Sent email to: johndoe1234@example.com. Body:
                Assurez-vous d'utiliser uniquement le français.

                Dans un royaume lointain, un roi bienveillant nommé Arjun luttait pour protéger son peuple d'un dragon destructeur.
                Malgré ses efforts, il ne pouvait pas vaincre la bête. Une jeune archère, Mira, a proposé son aide, affirmant qu'elle avait
                un plan pour tuer le dragon. Sceptique mais désespéré, Arjun a accepté. Mira a réussi à tuer le dragon avec une seule flèche,
                ramenant la paix dans le royaume. Reconnaissant, Arjun a demandé Mira en mariage, et ils ont régné ensemble sur le royaume,
                perpétuant l'héritage d'Arjun de justice et de compassion. Leur histoire s'est terminée heureusement, avec Mira se souvenant
                comme l'héroïne qui a sauvé le royaume.

                Execution complete in 31682 ms!


         */

    }


    private static async Task BookSamplesAsync(bool useStructuredPlanner = false)
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Book Creation Plan  ========");

        IKernel kernel;
        ISequentialPlanner planner;

        if (useStructuredPlanner)
        {
            kernel = InitializeKernelAndStructuredPlanner(out var structuredSequentialPlanner);
            var folder = RepoFiles.SampleSkillsPath();
            kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
            kernel.ImportSemanticSkillFromDirectory(folder, "MiscSkill");

            var originalPlan = await structuredSequentialPlanner.CreatePlanAsync("Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'");

            Console.WriteLine("Original plan:");
            Console.WriteLine(originalPlan.ToPlanWithGoalString());

            Stopwatch sw = new();
            sw.Start();
            await ExecutePlanAsync(kernel, originalPlan);
            sw.Stop();

            Console.WriteLine($"Execution complete in {sw.ElapsedMilliseconds} ms!");
        }
        else
        {
            kernel = InitializeKernelAndPlanner(out var sequentialPlanner);
            var folder = RepoFiles.SampleSkillsPath();
            kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
            kernel.ImportSemanticSkillFromDirectory(folder, "MiscSkill");
            var originalPlan = await sequentialPlanner.CreatePlanAsync("Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'");

            Console.WriteLine("Original plan:");
            Console.WriteLine(originalPlan.ToPlanWithGoalString());

            Stopwatch sw = new();
            sw.Start();
            await ExecutePlanAsync(kernel, originalPlan);
            sw.Stop();

            Console.WriteLine($"Execution complete in {sw.ElapsedMilliseconds} ms!");
        }

        // Load additional skills to enable planner to do non-trivial asks.
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticPluginFromDirectory(folder, "WriterSkill");
        kernel.ImportSemanticPluginFromDirectory(folder, "MiscSkill");

        /*
           Observed Output:

           Sequential planner output:
           Original plan:
           - Goal: Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'

           Steps:
           - WriterSkill.NovelOutline chapterCount='3' INPUT='A group of kids in a club called 'The Thinking Caps.'' endMarker='<!--===ENDPART===-->' => OUTLINE
           - WriterSkill.NovelChapter previousChapter='' theme='Children's Adventure' chapterIndex='1' INPUT='$OUTLINE[0]' => CHAPTER1
           - WriterSkill.NovelChapter previousChapter='$CHAPTER1' theme='Children's Adventure' chapterIndex='2' INPUT='$OUTLINE[1]' => CHAPTER2
           - WriterSkill.NovelChapter previousChapter='$CHAPTER2' theme='Children's Adventure' chapterIndex='3' INPUT='$OUTLINE[2]' => CHAPTER3
           - MiscSkill.Continue INPUT='$CHAPTER1' => RESULT__CHAPTER1
           - MiscSkill.Continue INPUT='$CHAPTER2' => RESULT__CHAPTER2
           - MiscSkill.Continue INPUT='$CHAPTER3' => RESULT__CHAPTER3

            Tokens:
            - CreatePlan: Total Tokens: 1731 Prompt Tokens: 1451 Completion Tokens: 280
            - WriterSkill.NovelOutline: Total Tokens: 738 Prompt Tokens: 133 Completion Tokens: 605
            - WriterSkill.NovelChapter: Total Tokens: 1033 Prompt Tokens: 676 Completion Tokens: 357
            - WriterSkill.NovelChapter: Total Tokens: 1459 Prompt Tokens: 1033 Completion Tokens: 426
            - WriterSkill.NovelChapter: Total Tokens: 1598 Prompt Tokens: 1102 Completion Tokens: 496
            - MiscSkill.Continue: Total Tokens: 675 Prompt Tokens: 375 Completion Tokens: 300
            - MiscSkill.Continue: Total Tokens: 861 Prompt Tokens: 444 Completion Tokens: 417
            - MiscSkill.Continue: Total Tokens: 622 Prompt Tokens: 514 Completion Tokens: 108
            - Totals:
                Total Tokens: 7967
                Prompt Tokens: 6118
                Completion Tokens: 1849

            Result:
            Step 1: Novel Outline
            - Chapter 1: "The Formation of the Thinking Caps"

               In the small town of Brainville, a group of five kids, each with their unique quirks, decide to form a club called 'The Thinking Caps.' The group includes the ever-curious and inventive leader, Max; the bookworm and trivia queen, Lily; the quiet but observant observer, Sam; the energetic and athletic, Alex; and the artistic and imaginative, Bella. They transform Max's treehouse into their secret meeting place, complete with a sign that reads "The Thinking Caps HQ."

               The chapter revolves around the formation of the club, the kids' individual introductions, and their first meeting. They decide that their mission will be to solve the mysteries of Brainville using their unique skills and intelligence. The chapter ends with them stumbling upon their first mystery: the case of the missing town statue, a beloved symbol of Brainville's history.

               <!--===ENDPART===-->

               Chapter 2: "The Case of the Missing Statue"

               The Thinking Caps are on their first mission: to find the missing town statue. The chapter begins with the kids gathering clues. Max uses his inventiveness to create a device that can detect metal, hoping it will lead them to the statue. Lily, with her vast knowledge, provides historical context about the statue and its significance. Sam, with his keen observation skills, notices a strange pattern of footprints at the statue's original location. Alex, with his athletic prowess, follows the footprints, leading them to a hidden part of the town park. Bella, with her artistic eye, recognizes a piece of graffiti at the park that matches a symbol they found near the statue's base.

               The chapter ends with the kids realizing that the statue was not stolen but hidden by a group of mischievous teenagers as a prank. The Thinking Caps manage to retrieve the statue and return it to its rightful place, earning the gratitude of the town.

               <!--===ENDPART===-->

               Chapter 3: "The Thinking Caps and the Brainville Bandit"

               After their success with the statue, the Thinking Caps become local heroes. Their next mystery, however, is a bit more personal. Someone has been stealing snacks from their treehouse HQ! The kids decide to catch the thief, dubbed the "Brainville Bandit."

               Max invents a snack-detecting alarm system, Lily researches common thieving patterns, Sam keeps a close eye on the treehouse, Alex sets up physical traps around the HQ, and Bella creates a decoy snack box to lure the thief. After a hilarious series of events, they discover that the "Brainville Bandit" is actually a squirrel who found a way into their treehouse.

               The chapter ends with the kids laughing at their over-the-top response to a simple squirrel, but they are happy to have solved another mystery. They realize that no matter how big or small the problem, they can always rely on their intelligence and teamwork to find a solution.

                <!--===ENDPART===-->

              Step 2: Novel Chapter:
               - "The Formation of the Thinking Caps"

                   In the quaint, bustling town of Brainville, five children with distinct personalities and unique talents decided to form a club. They named it 'The Thinking Caps.' The group was as diverse as it was dynamic, each member bringing something special to the table.

                   Max, the leader of the group, was an inventive whizz-kid. His mind was a treasure trove of ideas, and he could turn the most ordinary objects into extraordinary inventions. Lily, the trivia queen, was a bookworm with an insatiable thirst for knowledge. She could recite facts about anything and everything, making her the go-to person for any information.

                   Sam was the quiet one, but his silence was not a sign of disinterest. He was an observer, always watching, always noticing things that others missed. Alex was the athlete of the group, his energy and agility unmatched. He could outrun anyone in Brainville and was always ready for a physical challenge. Bella, the artist, saw the world through a creative lens. Her imagination was boundless, and she could create beautiful art from the simplest of things.

                   Their secret meeting place was Max's treehouse, which they transformed into 'The Thinking Caps HQ.' The treehouse was adorned with a sign that read the club's name, and it was filled with all sorts of gadgets, books, art supplies, and sports equipment.

                   Their mission was clear: to use their unique skills and intelligence to solve the mysteries of Brainville. As they sat in their newly formed HQ, discussing their plans, they stumbled upon their first mystery. The town statue, a beloved symbol of Brainville's history, had gone missing. The Thinking Caps were on the case, ready to put their minds to the test.

               Step 3 - Novel Chapter:
                   - "The Case of the Missing Statue"

                   The morning sun shone brightly on the Thinking Caps HQ as the five friends gathered for their first official mission. The town statue, a symbol of Brainville's rich history, had mysteriously disappeared overnight. The town was in an uproar, and the Thinking Caps were ready to solve the mystery.

                   Max, with his inventive mind, had created a device that could detect metal. He hoped that it would lead them to the statue. "This should help us find the statue if it's still in town," he said, holding up a gadget that looked like a cross between a remote control and a metal detector.

                   Lily, with her vast knowledge, provided some historical context. "The statue was made of bronze and was erected to commemorate the founding of Brainville," she explained, her eyes sparkling with excitement. "It's not just a statue; it's a piece of our history."

                   Sam, the observer, had noticed something unusual at the statue's original location. "Look at these footprints," he said, pointing at the ground. "They're too big to be any of ours, and they lead away from the statue's base."

                   Alex, the athlete, was quick to act. He followed the footprints, his agile body moving swiftly. The footprints led them to a hidden part of the town park, a place they had never explored before.

                   Bella, with her artistic eye, noticed something peculiar. "Look at this graffiti," she said, pointing at a symbol spray-painted on a wall. "It matches the symbol we found near the statue's base."

                   The pieces of the puzzle were coming together. The statue wasn't stolen; it was hidden. A group of mischievous teenagers had played a prank on the town. With the help of the Thinking Caps, the statue was retrieved and returned to its rightful place.

                   The town breathed a sigh of relief, and the Thinking Caps were hailed as heroes. Their first mission was a success, and they couldn't wait for their next adventure. Little did they know, it was just around the corner.

               Step 4 - Novel Chapter:
                - "The Thinking Caps and the Brainville Bandit"

                   The sun was setting on another day in Brainville, casting long shadows over the Thinking Caps' treehouse HQ. The five friends were gathered inside, their faces lit by the warm glow of a single lamp. They were celebrating their recent success with a feast of their favorite snacks. However, their celebration was cut short when they discovered that their snack stash was mysteriously depleting.

                   "Who could be stealing our snacks?" Bella asked, her eyes wide with surprise. "We're the only ones who know about this place."

                   Max, always the inventor, had an idea. "I can create a snack-detecting alarm system," he said, his eyes gleaming with excitement. "It will alert us when someone tries to take our snacks."

                   Lily, the trivia queen, decided to use her knowledge to help. "I'll research common thieving patterns," she said, already pulling out her notebook and pen. "Maybe we can predict when the thief will strike next."

                   Sam, the observer, decided to keep a close eye on the treehouse. "I'll watch the HQ," he said, his gaze steady and determined. "If anyone tries to sneak in, I'll catch them."

                   Alex, the athlete, was ready to take action. "I'll set up physical traps around the HQ," he said, flexing his muscles. "No one will be able to get in without us knowing."

                   Bella, the artist, had a creative solution. "I'll create a decoy snack box," she said, her eyes sparkling with mischief. "When the thief tries to take it, we'll catch them red-handed."

                   With their plan in place, the Thinking Caps set to work. After a series of hilarious events involving false alarms, a few minor mishaps with the traps, and a lot of teamwork, they finally caught the thief. To their surprise, the "Brainville Bandit" was a squirrel who had found a way into their treehouse.

                   The friends couldn't help but laugh at their over-the-top response to a simple squirrel. But they were happy to have solved another mystery. As they cleaned up their traps and restocked their snacks, they realized that no matter how big or small the problem, they could always rely on their intelligence and teamwork to find a solution. The Brainville Bandit was no more, and the Thinking Caps were ready for their next adventure.

               Step 5 - MiscSkill.Continue:

                - The children immediately started brainstorming, each contributing their unique skills to the problem. Max began sketching out a blueprint of the town square where the statue once stood, using his inventiveness to think of possible ways it could have been moved. Lily, with her vast knowledge, started recalling historical facts about the statue, hoping to find a clue in its past.

                   Sam, the observer, suggested they visit the site to look for overlooked details. Alex, with his athletic abilities, was ready to scout the area quickly and efficiently. Bella, the artist, decided to create a detailed sketch of the statue from memory, hoping it might reveal something they had missed.

                   As they worked together, they discovered that despite their differences, they made a great team. Each of them had a unique way of thinking, and when combined, they could tackle any problem that came their way.

                   The mystery of the missing statue was just the beginning for The Thinking Caps. As they delved deeper into the enigma, they realized that Brainville was full of mysteries waiting to be solved. And they were just the right team to do it.

                   Their adventures were filled with challenges, but also laughter, friendship, and the joy of discovery. The Thinking Caps, with their diverse skills and unique perspectives, proved that when we work together, we can achieve anything. And so, the legend of The Thinking Caps began, their stories echoing through the streets of Brainville, inspiring others to think, explore, and solve.

               Step 6 - MiscSkill.Continue:

                   "The Case of the Haunted Library"

                   The sun had set on Brainville, and the Thinking Caps were ready for their next mission. The town library, a place of knowledge and tranquility, was reportedly haunted. Books were flying off the shelves, lights were flickering, and eerie sounds echoed through the halls. The town was terrified, and the Thinking Caps were ready to uncover the truth.

                   Max, with his inventive mind, had created a device that could detect unusual energy fields. "This should help us find any ghostly activity," he said, holding up a gadget that looked like a cross between a flashlight and a radar.

                   Lily, with her vast knowledge, provided some historical context. "The library was built on an old cemetery," she explained, her eyes wide with intrigue. "There have been reports of hauntings ever since it was constructed."

                   Sam, the observer, had noticed something unusual at the library's entrance. "Look at these scratches," he said, pointing at the wooden door. "They're too irregular to be made by a human."

                   Alex, the athlete, was quick to act. He ventured into the library, his athletic body ready for any sudden movements. The scratches led them to a secluded section of the library, a place filled with ancient books.

                   Bella, with her artistic eye, noticed something peculiar. "Look at this pattern," she said, pointing at a symbol etched into the floor. "It matches the symbol we found on the door."

                   The pieces of the puzzle were coming together. The library wasn't haunted; it was disturbed. A group of raccoons had found their way into the library through a broken window and were causing all the chaos. With the help of the Thinking Caps, the raccoons were safely removed, and the library was restored to its peaceful state.

                   The town breathed a sigh of relief, and the Thinking Caps were hailed as heroes once again. Their second mission was a success, and they eagerly awaited their next adventure. Little did they know, it was just around the corner.

               Step 7 - MiscSkill.Continue:

                - This is a delightful story! It's a great example of a children's tale that combines humor, adventure, and lessons about teamwork and problem-solving. The characters are well-defined, each with their own unique skills and personalities, and the plot is engaging and fun. The surprise twist at the end, with the thief being a squirrel, adds a nice touch of humor and lightness. The story also subtly teaches children about the importance of not jumping to conclusions and the value of using different skills and approaches to solve a problem. Well done!


              Execution complete in 227562 ms!


              Structured sequential planner output:
                Original plan:
               Goal: Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'

               Steps:
               - WriterSkill.NovelOutline INPUT='A group of kids in a club called 'The Thinking Caps.'' endMarker='END' chapterCount='3' => OUTLINE
               - WriterSkill.NovelChapter INPUT='$OUTLINE[0]' previousChapter='' theme='A group of kids in a club called 'The Thinking Caps.'' chapterIndex='1' => CHAPTER1
               - WriterSkill.NovelChapter INPUT='$OUTLINE[1]' previousChapter='$CHAPTER1' theme='A group of kids in a club called 'The Thinking Caps.'' chapterIndex='2' => CHAPTER2
               - WriterSkill.NovelChapter INPUT='$OUTLINE[2]' previousChapter='$CHAPTER2' theme='A group of kids in a club called 'The Thinking Caps.'' chapterIndex='3' => CHAPTER3

               Tokens:
               - CreatePlan: Total Tokens: 1587 Prompt Tokens: 1002 Completion Tokens: 585
                - WriterSkill.NovelOutline: Total Tokens: 639 Prompt Tokens: 129 Completion Tokens: 510
                - WriterSkill.NovelChapter: Total Tokens: 1006 Prompt Tokens: 590 Completion Tokens: 416
                - WriterSkill.NovelChapter: Total Tokens: 1459 Prompt Tokens: 1006 Completion Tokens: 453
                - WriterSkill.NovelChapter: Total Tokens: 1537 Prompt Tokens: 1043 Completion Tokens: 494
                - Totals:
                    Total Tokens: 4633
                    Prompt Tokens: 3770
                    Completion Tokens: 863


                Result:

                Step 1: Novel Outline
                - Title: The Thinking Caps' Grand Adventure

                   Chapter 1: The Mysterious Map

                   In the small town of Brainville, a group of five kids, known as 'The Thinking Caps,' meet in their treehouse headquarters. The members include the leader, Max, a natural-born problem solver; Lily, the bookworm with a photographic memory; Sam, the tech whiz; Mia, the artist with a wild imagination; and Charlie, the quiet one with an uncanny knack for noticing things others miss. One day, they discover an old, cryptic map hidden in a book that Lily borrowed from the library. The map points to a location within Brainville, sparking curiosity and excitement among the group. They decide to investigate, setting the stage for a grand adventure. The chapter ends with the kids preparing for their journey, each contributing their unique skills to the plan.

                   END

                   Chapter 2: The Secret of Brainville

                   The second chapter begins with 'The Thinking Caps' embarking on their adventure. They follow the map through Brainville, solving riddles and overcoming obstacles along the way. Max's leadership and problem-solving skills, Lily's knowledge, Sam's tech gadgets, Mia's creative thinking, and Charlie's keen observation skills all come into play. The journey leads them to a hidden part of the town library, where they discover a secret room filled with ancient books and artifacts. They learn about the town's forgotten history and the legendary Brainville Thinkers, a group of child prodigies who used their intelligence to save the town from various crises. The chapter ends with the kids realizing that they are the modern-day Brainville Thinkers, destined to carry on the legacy.

                   END

                   Chapter 3: The Thinking Caps to the Rescue

                   In the final chapter, a crisis hits Brainville - the town's power supply is mysteriously cut off. The Thinking Caps, inspired by the Brainville Thinkers, decide to solve the problem. Using their combined skills, they trace the power outage to an old, abandoned power station. They discover that the power cut is due to a malfunctioning machine. Sam's tech skills come in handy as he fixes the machine, while the others fend off a group of mischievous raccoons that caused the malfunction in the first place. The kids manage to restore the power, saving the day. The chapter ends with the town celebrating the Thinking Caps as heroes, and the kids realizing that their adventure was just the beginning of their journey as the new Brainville Thinkers.

                   END

                Step 2: Novel Chapter:
                - In the quaint, intellectual town of Brainville, a group of five extraordinary kids, collectively known as 'The Thinking Caps,' convened in their treehouse headquarters. The treehouse, nestled in the heart of a grand old oak, was their sanctuary, a place where their minds could roam free and their ideas could take flight.

                   Max, the leader of the group, was a natural-born problem solver. His mind was a labyrinth of solutions, always ready to tackle the next challenge. Lily, the bookworm, had a memory as sharp as a tack, able to recall information from books she'd read years ago. Sam, the tech whiz, could make gadgets out of anything, his fingers dancing over wires and circuits like a maestro. Mia, the artist, saw the world in vibrant colors and shapes, her imagination as boundless as the sky. And then there was Charlie, the quiet one, whose eyes missed nothing, his observations often the key to solving their most complex problems.

                   One sunny afternoon, they stumbled upon an intriguing mystery. Lily, while flipping through a book she'd borrowed from the library, discovered an old, cryptic map tucked between its pages. The map, worn and faded, pointed to a location within Brainville. The sight of the map ignited a spark of curiosity and excitement among the group. They huddled around the map, their eyes wide with anticipation.

                   Max, with his strategic mind, immediately started planning their route. Lily, recalling a similar map from one of her books, provided historical context. Sam, with his tech gadgets, promised to create a device to help them navigate. Mia, with her creative thinking, suggested they prepare for all possible scenarios. And Charlie, ever observant, pointed out landmarks on the map that others had missed.

                   As the sun set, casting long shadows over Brainville, the kids prepared for their journey. They knew not what awaited them, but they were ready. Their minds were sharp, their spirits high. This was the beginning of their grand adventure, and they could hardly wait for dawn.

                Step 3 - Novel Chapter:
                - "The Secret of Brainville"

                   As the first rays of dawn pierced the morning fog, the Thinking Caps set off on their grand adventure. The cryptic map, now safely encased in a plastic cover, was their guide through the winding streets of Brainville. Max, with his strategic mind, led the way, his eyes scanning the map and the surroundings. Lily, her mind a treasure trove of information, provided historical insights about the landmarks they passed. Sam, armed with his tech gadgets, had created a device that beeped when they were on the right track. Mia, with her sketchbook in hand, captured the journey in vibrant colors, while Charlie, ever observant, kept an eye out for anything unusual.

                   Their journey led them through the heart of Brainville, past the bustling market, the serene park, and the towering town hall. They solved riddles etched in the corners of the map, navigated through hidden alleys, and overcame obstacles that stood in their way. Each challenge they faced was met with a combination of their unique skills, their camaraderie growing with each step they took.

                   Finally, their journey led them to an unexpected place - the town library. But it wasn't the part of the library they were familiar with. Hidden behind a bookshelf, they discovered a secret room filled with ancient books and artifacts. The room, dusty and untouched, was a testament to Brainville's forgotten history.

                   As they explored the room, they stumbled upon a book that told the tale of the legendary Brainville Thinkers, a group of child prodigies who used their intelligence to save the town from various crises. The stories resonated with the Thinking Caps, their eyes wide with realization.

                   As the sun set, casting a warm glow over the secret room, the kids looked at each other. They were the modern-day Brainville Thinkers, destined to carry on the legacy. Their adventure had led them to a part of their town's history they never knew existed, and to a part of themselves they never knew they had. As they left the library, the map safely tucked away, they knew their journey was far from over. This was just the beginning of their legacy as the new Brainville Thinkers.

                Step 4 - Novel Chapter:
                - "The Thinking Caps to the Rescue"

                   As the sun rose over Brainville, the town was unusually quiet. The usual hum of electricity was absent, replaced by an eerie silence. The power was out, and the town was plunged into darkness. The Thinking Caps, fresh from their adventure in the library, knew they had a new challenge to face.

                   Max, Lily, Sam, Mia, and Charlie gathered in their treehouse headquarters, the cryptic map spread out before them. The town needed their help, and they were ready to step up. Inspired by the tales of the Brainville Thinkers, they knew they had the skills to solve the crisis.

                   Max, with his strategic mind, took charge, organizing the group and formulating a plan. Lily, her mind filled with knowledge from countless books, suggested they investigate the old power station at the edge of town. Sam, the tech whiz, was excited at the prospect of tinkering with the town's power supply. Mia, with her creative thinking, proposed a way to distract the townsfolk while they worked. And Charlie, ever observant, noticed a trail of small paw prints leading towards the power station.

                   Following the paw prints, they arrived at the power station. It was old and abandoned, a relic from a bygone era. Inside, they found the source of the problem - a group of mischievous raccoons had found their way into the station and caused a malfunction in the machinery.

                   Sam, with his tech gadgets, got to work on the machine. His fingers flew over the controls, adjusting wires and recalibrating systems. Meanwhile, Max, Lily, Mia, and Charlie worked together to gently usher the raccoons out of the power station, using a combination of food lures and gentle nudging.

                   With a final twist of a wrench, Sam fixed the machine. The power station hummed back to life, and the lights in Brainville flickered on, one by one. The town was saved, and it was all thanks to the Thinking Caps.

                   As they returned to their treehouse, the kids were greeted with cheers from the townsfolk. They had saved the day, just like the Brainville Thinkers of old. As they looked at each other, they knew this was just the beginning. They were the new Brainville Thinkers, ready to face whatever challenges came their way. Their grand adventure was far from over. It was just getting started.


                    Execution complete in 119313 ms!

         */
    }


    private static async Task MemorySampleAsync(bool useStructuredPlanner = false)
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Plan using Memory ========");

        var kernel = InitializeKernelWithMemory();

        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticPluginFromDirectory(folder,
           "SummarizeSkill",
           "WriterSkill",
           "CalendarSkill",
           "ChatSkill",
           "ChildrensBookSkill",
           "ClassificationSkill",
           "CodingSkill",
           "FunSkill",
           "IntentDetectionSkill",
           "MiscSkill",
           "QASkill");

        kernel.ImportPlugin(new EmailSkill(), "email");
        kernel.ImportPlugin(new StaticTextPlugin(), "statictext");
        kernel.ImportPlugin(new TextPlugin(), "coretext");

        var goal = "Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'";

        // IMPORTANT: To use memory and embeddings to find relevant skills in the planner, set the 'Memory' property on the planner config.
        if (!useStructuredPlanner)
        {
            var planner = new SequentialPlanner(kernel, new SequentialPlannerConfig { RelevancyThreshold = 0.5, Memory = kernel.Memory });
            var plan = await planner.CreatePlanAsync(goal);

            Console.WriteLine("Original plan:");
            Console.WriteLine(plan.ToPlanWithGoalString());
        }

        else
        {
            var planner = new StructuredSequentialPlanner(kernel, new StructuredPlannerConfig() { RelevancyThreshold = 0.5, Memory = kernel.Memory });
            var plan = await planner.CreatePlanAsync(goal);

            Console.WriteLine("Original plan:");
            Console.WriteLine(plan.ToPlanWithGoalString());
        }

        /*
           Observed Output:
           Sequential planner output:
           Original plan:
           Goal: Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'

           Steps:
           - WriterSkill.NovelOutline chapterCount='3' endMarker='<!--===ENDPART===-->' INPUT='A group of kids in a club called 'The Thinking Caps.'' => OUTLINE
           - WriterSkill.NovelChapter previousChapter='' theme='Children's Adventure' chapterIndex='1' INPUT='$OUTLINE[0]' => CHAPTER1
           - WriterSkill.NovelChapter previousChapter='' theme='Children's Adventure' chapterIndex='2' INPUT='$OUTLINE[1]' => CHAPTER2
           - WriterSkill.NovelChapter previousChapter='' theme='Children's Adventure' chapterIndex='3' INPUT='$OUTLINE[2]' => CHAPTER3
           - coretext.Concat input2='$CHAPTER2' INPUT='$CHAPTER1' => TEMP_BOOK
           - coretext.Concat input2='$CHAPTER3' INPUT='$TEMP_BOOK' => RESULT__BOOK

           Total Tokens: 2843 Prompt Tokens: 2573 Completion Tokens: 270

           Structured sequential planner output:
           Original plan:
            Goal: Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'

           Steps:
           - WriterSkill.NovelOutline chapterCount='3' endMarker='End of Chapter' INPUT='A group of kids in a club called 'The Thinking Caps.'' => OUTLINE
           - WriterSkill.NovelChapter previousChapter='' chapterIndex='1' INPUT='$OUTLINE[0]' theme='Children's Adventure' => CHAPTER1
           - WriterSkill.NovelChapter previousChapter='$CHAPTER1' chapterIndex='2' INPUT='$OUTLINE[1]' theme='Children's Adventure' => CHAPTER2
           - WriterSkill.NovelChapter previousChapter='$CHAPTER2' chapterIndex='3' INPUT='$OUTLINE[2]' theme='Children's Adventure' => CHAPTER3
           - coretext.Concat INPUT='$CHAPTER1' input2='$CHAPTER2' => BOOK_PART1
           - coretext.Concat INPUT='$BOOK_PART1' input2='$CHAPTER3' => BOOK

           Total Tokens: 2194 Prompt Tokens: 1523 Completion Tokens: 671
         */
    }


    private static IKernel InitializeKernelAndPlanner(out SequentialPlanner planner, int maxTokens = 1024)
    {
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        planner = new SequentialPlanner(kernel, new SequentialPlannerConfig { MaxTokens = maxTokens });

        return kernel;
    }


    private static IKernel InitializeKernelAndStructuredPlanner(out StructuredSequentialPlanner planner, int maxTokens = 1024)
    {
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        planner = new StructuredSequentialPlanner(kernel, new StructuredPlannerConfig() { MaxTokens = maxTokens });

        return kernel;
    }


    private static IKernel InitializeKernelWithMemory()
    {
        // IMPORTANT: Register an embedding generation service and a memory store. The Planner will
        // use these to generate and store embeddings for the function descriptions.
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .WithAzureTextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                TestConfiguration.AzureOpenAIEmbeddings.ApiKey)
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();
        return kernel;
    }


    private static ISemanticTextMemory GetMemory(IKernel? kernel = null)
    {
        if (kernel is not null)
        {
            return kernel.Memory;
        }
        var memoryStorage = new VolatileMemoryStore();
        var textEmbeddingGenerator = new Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding.AzureTextEmbeddingGeneration(
            TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            TestConfiguration.AzureOpenAIEmbeddings.ApiKey);

        // var textEmbeddingGenerator = new Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding.OpenAITextEmbeddingGeneration(
        //     TestConfiguration.OpenAI.EmbeddingModelId,
        //     TestConfiguration.OpenAI.ApiKey);

        var memory = new SemanticTextMemory(memoryStorage, textEmbeddingGenerator);
        return memory;
    }


    private static async Task<Plan> ExecutePlanAsync(
        IKernel kernel,
        Plan plan,
        string input = "",
        int maxSteps = 10)
    {
        Stopwatch sw = new();
        sw.Start();

        // loop until complete or at most N steps
        try
        {
            for (var step = 1; plan.HasNextStep && step < maxSteps; step++)
            {
                if (string.IsNullOrEmpty(input))
                {
                    await plan.InvokeNextStepAsync(kernel.CreateNewContext());
                    // or await kernel.StepAsync(plan);
                }
                else
                {
                    plan = await kernel.StepAsync(input, plan);
                    input = string.Empty;
                }

                if (!plan.HasNextStep)
                {
                    Console.WriteLine($"Step {step} - COMPLETE!");
                    Console.WriteLine(plan.State.ToString());
                    break;
                }

                Console.WriteLine($"Step {step} - Results so far:");
                Console.WriteLine(plan.State.ToString());
            }
        }
        catch (SKException e)
        {
            Console.WriteLine("Step - Execution failed:");
            Console.WriteLine(e.Message);
        }

        sw.Stop();
        Console.WriteLine($"Execution complete in {sw.ElapsedMilliseconds} ms!");
        return plan;
    }
}
