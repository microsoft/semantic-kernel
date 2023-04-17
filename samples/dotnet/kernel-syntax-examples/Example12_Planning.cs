// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;
using Skills;
using TextSkill = Skills.TextSkill;

// ReSharper disable once InconsistentNaming
internal static class Example12_Planning
{
    public static async Task RunAsync()
    {
        await PoetrySamplesAsync();
        await EmailSamplesAsync();
        await BookSamplesAsync();
        await MemorySampleAsync();
        await IfConditionalSampleAsync();
        await WhileConditionalSampleAsync();
    }

    private static async Task IfConditionalSampleAsync()
    {
        Console.WriteLine("======== Planning - If/Else Conditional flow example ========");
        var kernel = InitializeKernelAndPlanner(out var planner);

        // Load additional skills to enable planner to do non-trivial asks.
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "FunSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
        kernel.ImportSkill(new TimeSkill());

        var originalPlan = await kernel.RunAsync(
            @"If is still morning please give me a joke about coffee otherwise tell me one about afternoon, but if its night give me a poem about the moon",
            planner["CreatePlan"]);

        /*
        <goal>If is still morning please give me a joke about coffee otherwise tell me one about afternoon, but if its night give me a poem about the moon</goal>
        <plan>
          <function._GLOBAL_FUNCTIONS_.HourNumber setContextVariable="CURRENT_HOUR"/>
          <if condition="$CURRENT_HOUR lessthan 12">
            <function.FunSkill.Joke input="coffee"/>
          </if>
          <else>
            <if condition="$CURRENT_HOUR lessthan 18">
              <function.FunSkill.Joke input="afternoon"/>
            </if>
            <else>
              <function.FunSkill.ShortPoem input="the moon"/>
            </else>
          </else>
        </plan>
        */

        Console.WriteLine("Original plan:");
        Console.WriteLine(originalPlan.Variables.ToPlan().PlanString);

        await ExecutePlanAsync(kernel, planner, originalPlan, 20);
    }

    private static async Task WhileConditionalSampleAsync()
    {
        Console.WriteLine("======== Planning - While Loop Conditional flow example ========");
        var kernel = InitializeKernelAndPlanner(out var planner);

        // Load additional skills to enable planner to do non-trivial asks.
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "FunSkill");
        kernel.ImportSkill(new MathSkill());
        kernel.ImportSkill(new TimeSkill());

        var originalPlan = await kernel.RunAsync(
            @"Start with a X number equals to the current minutes of the clock and remove 20 from this number until it becomes 0. After that tell me a math style joke where the input is X number + ""bananas""",
            planner["CreatePlan"]);

        /*
        <goal>
        Start with a X number equals to the current minutes of the clock and remove 20 from this number until it becomes 0. After that tell me a math style joke where the input is X number + "bananas"
        </goal>
        <plan>
          <function._GLOBAL_FUNCTIONS_.Minute setContextVariable="X_NUMBER"/>
          <while condition="$X_NUMBER greaterthan 0">
            <function._GLOBAL_FUNCTIONS_.Subtract input="$X_NUMBER" Amount="20" setContextVariable="X_NUMBER"/>
          </while>
          <function.FunSkill.Joke input="$X_NUMBER bananas" style="Math" appendToResult="RESULT__JOKE"/>
        </plan>
        */

        Console.WriteLine("Original plan:");
        Console.WriteLine(originalPlan.Variables.ToPlan().PlanString);

        await ExecutePlanAsync(kernel, planner, originalPlan, 20);
    }

    private static async Task PoetrySamplesAsync()
    {
        Console.WriteLine("======== Planning - Create and Execute Poetry Plan ========");
        var kernel = InitializeKernelAndPlanner(out var planner);

        // Load additional skills to enable planner to do non-trivial asks.
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");

        var originalPlan = await kernel.RunAsync("Write a poem about John Doe, then translate it into Italian.", planner["CreatePlan"]);
        // <goal>
        // Write a poem about John Doe, then translate it into Italian.
        // </goal>
        // <plan>
        //   <function.WriterSkill.ShortPoem input="John Doe is a kind and generous man who loves to help others and make them smile."/>
        //   <function.WriterSkill.Translate language="Italian"/>
        // </plan>

        Console.WriteLine("Original plan:");
        Console.WriteLine(originalPlan.Variables.ToPlan().PlanString);

        await ExecutePlanAsync(kernel, planner, originalPlan, 5);
    }

    private static async Task EmailSamplesAsync()
    {
        Console.WriteLine("======== Planning - Create and Execute Email Plan ========");
        var kernel = InitializeKernelAndPlanner(out var planner, 512);
        kernel.ImportSkill(new EmailSkill(), "email");

        // Load additional skills to enable planner to do non-trivial asks.
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");

        var originalPlan = await kernel.RunAsync("Summarize an input, translate to french, and e-mail to John Doe", planner["CreatePlan"]);
        // <goal>
        // Summarize an input, translate to french, and e-mail to John Doe
        // </goal>
        // <plan>
        //   <function.SummarizeSkill.Summarize/>
        //   <function.WriterSkill.Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
        //   <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
        //   <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
        // </plan>

        Console.WriteLine("Original plan:");
        Console.WriteLine(originalPlan.Variables.ToPlan().PlanString);

        var executionResults = originalPlan;
        executionResults.Variables.Update(
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
            "happily ever after, with the people of the kingdom remembering Mira as the brave young woman who saved them from the dragon.");
        await ExecutePlanAsync(kernel, planner, executionResults, 5);
    }

    private static async Task BookSamplesAsync()
    {
        Console.WriteLine("======== Planning - Create and Execute Book Creation Plan  ========");
        var kernel = InitializeKernelAndPlanner(out var planner);

        // Load additional skills to enable planner to do non-trivial asks.
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");

        var originalPlan = await kernel.RunAsync(
            "Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'",
            planner["CreatePlan"]);
        // <goal>
        // Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'
        // </goal>
        // <plan>
        //   <function.WriterSkill.NovelOutline input="A group of kids in a club called 'The Thinking Caps' solve mysteries and puzzles using their creativity and logic." chapterCount="3" endMarker="***" setContextVariable="OUTLINE" />
        //   <function.planning.BucketOutputs input="$OUTLINE" bucketCount="3" bucketLabelPrefix="CHAPTER" />
        //   <function.WriterSkill.NovelChapter input="$CHAPTER_1" theme="Mystery" chapterIndex="1" appendToResult="CHAPTER_1_TEXT" />
        //   <function.WriterSkill.NovelChapter input="$CHAPTER_2" theme="Mystery" previousChapter="$CHAPTER_1" chapterIndex="2" appendToResult="CHAPTER_2_TEXT" />
        //   <function.WriterSkill.NovelChapter input="$CHAPTER_3" theme="Mystery" previousChapter="$CHAPTER_2" chapterIndex="3" appendToResult="CHAPTER_3_TEXT" />
        // </plan>

        Console.WriteLine("Original plan:");
        Console.WriteLine(originalPlan.Variables.ToPlan().PlanString);

        Stopwatch sw = new();
        sw.Start();
        await ExecutePlanAsync(kernel, planner, originalPlan);
    }

    private static async Task MemorySampleAsync()
    {
        Console.WriteLine("======== Planning - Create and Execute Plan using Memory ========");

        var kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            .Configure(
                config =>
                {
                    config.AddAzureTextCompletionService(
                        Env.Var("AZURE_OPENAI_SERVICE_ID"),
                        Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
                        Env.Var("AZURE_OPENAI_ENDPOINT"),
                        Env.Var("AZURE_OPENAI_KEY"));

                    config.AddAzureTextEmbeddingGenerationService(
                        Env.Var("AZURE_OPENAI_EMBEDDINGS_SERVICE_ID"),
                        Env.Var("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME"),
                        Env.Var("AZURE_OPENAI_EMBEDDINGS_ENDPOINT"),
                        Env.Var("AZURE_OPENAI_EMBEDDINGS_KEY"));
                })
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        // Load native skill into the kernel skill collection, sharing its functions with prompt templates
        var planner = kernel.ImportSkill(new PlannerSkill(kernel), "planning");

        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "CalendarSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "ChatSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "ChildrensBookSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "ClassificationSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "CodingSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "FunSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "IntentDetectionSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "MiscSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "QASkill");

        kernel.ImportSkill(new EmailSkill(), "email");
        kernel.ImportSkill(new StaticTextSkill(), "statictext");
        kernel.ImportSkill(new TextSkill(), "text");
        kernel.ImportSkill(new Microsoft.SemanticKernel.CoreSkills.TextSkill(), "coretext");

        var context = new ContextVariables("Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'");
        context.Set(PlannerSkill.Parameters.RelevancyThreshold, "0.78");

        var executionResults = await kernel.RunAsync(context, planner["CreatePlan"]);

        Console.WriteLine("Original plan:");
        Console.WriteLine(executionResults.Variables.ToPlan().PlanString);
    }

    private static IKernel InitializeKernelAndPlanner(out IDictionary<string, ISKFunction> planner, int maxTokens = 1024)
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddAzureTextCompletionService(
            Env.Var("AZURE_OPENAI_SERVICE_ID"),
            Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        // Load native skill into the kernel skill collection, sharing its functions with prompt templates
        planner = kernel.ImportSkill(new PlannerSkill(kernel, maxTokens), "planning");
        return kernel;
    }

    private static async Task<SKContext> ExecutePlanAsync(
        IKernel kernel,
        IDictionary<string, ISKFunction> planner,
        SKContext executionResults,
        int maxSteps = 10)
    {
        Stopwatch sw = new();
        sw.Start();

        // loop until complete or at most N steps
        for (int step = 1; !executionResults.Variables.ToPlan().IsComplete && step < maxSteps; step++)
        {
            var results = await kernel.RunAsync(executionResults.Variables, planner["ExecutePlan"]);
            if (results.Variables.ToPlan().IsSuccessful)
            {
                Console.WriteLine($"Step {step} - Execution results:");
                Console.WriteLine(results.Variables.ToPlan().PlanString);

                if (results.Variables.ToPlan().IsComplete)
                {
                    Console.WriteLine($"Step {step} - COMPLETE!");
                    Console.WriteLine(results.Variables.ToPlan().Result);

                    // Console.WriteLine("VARIABLES: ");
                    // Console.WriteLine(string.Join("\n\n", results.Variables.Select(v => $"{v.Key} = {v.Value}")));
                    break;
                }

                // Console.WriteLine($"Step {step} - Results so far:");
                // Console.WriteLine(results.ToPlan().Result);
            }
            else
            {
                Console.WriteLine($"Step {step} - Execution failed:");
                Console.WriteLine(results.Variables.ToPlan().Result);
                break;
            }

            executionResults = results;
        }

        sw.Stop();
        Console.WriteLine($"Execution complete in {sw.ElapsedMilliseconds} ms!");
        return executionResults;
    }
}

// ReSharper disable CommentTypo
/* Example Output:

======== Planning - Create and Execute Poetry Plan ========
Original plan:
<goal>
Write a poem about John Doe, then translate it into Italian.
</goal>
<plan>
  <function.WriterSkill.ShortPoem input="John Doe is a kind and generous man who loves to help others and make them smile."/>
  <function.WriterSkill.Translate language="Italian"/>
</plan>
Step 1 - Execution results:
<goal>
Write a poem about John Doe, then translate it into Italian.
</goal><plan>
  <function.WriterSkill.Translate language="Italian" />
</plan>
Step 2 - Execution results:
<goal>
Write a poem about John Doe, then translate it into Italian.
</goal><plan>
</plan>
Step 2 - COMPLETE!
John Doe è un uomo di grande cuore e grazia
Ha sempre un sorriso sul volto
Aiuta i poveri, i malati e i vecchi
Ma a volte la sua bontà lo mette nei guai
Come quando ha dato il suo cappotto a un tremante

- There once was a girl named Alice
Who loved to explore and be curious
She followed a rabbit down a burrow
And found a world of wonder and magic
But also of danger and madness

C'era una volta una ragazza di nome Alice
Che amava esplorare e essere curiosa
Seguì un coniglio in una buca
E trovò un mondo di meraviglia e magia
Ma anche di pericolo e follia

- Roses are red, violets are blue
Sugar is sweet, and so are you
But roses have thorns, and violets can fade
Sugar can spoil, and you can betray
So don't trust the words, but the actions that prove

Le rose sono rosse, le viole sono blu
Lo zucchero è dolce, e così sei tu
Ma le rose hanno spine, e le
Execution complete in 15223 ms!
======== Planning - Create and Execute Email Plan ========
Original plan:
<goal>
Summarize an input, translate to french, and e-mail to John Doe
</goal>
<plan>
    <function.SummarizeSkill.Summarize/>
    <function.WriterSkill.Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
</plan>
Step 1 - Execution results:
<goal>
Summarize an input, translate to french, and e-mail to John Doe
</goal><plan>
  <function.WriterSkill.Translate language="French" setContextVariable="TRANSLATED_SUMMARY" />
  <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS" />
  <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS" />
</plan>
Step 2 - Execution results:
<goal>
Summarize an input, translate to french, and e-mail to John Doe
</goal><plan>
  <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS" />
  <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS" />
</plan>
Step 3 - Execution results:
<goal>
Summarize an input, translate to french, and e-mail to John Doe
</goal><plan>
  <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS" />
</plan>
Step 4 - Execution results:
<goal>
Summarize an input, translate to french, and e-mail to John Doe
</goal><plan>
</plan>
Step 4 - COMPLETE!
Sent email to: johndoe1234@example.com. Body: Some possible translations are:

- Mira, une archère habile, tue un dragon et épouse le roi qui régnait avec bonté.
- Un roi bienveillant et une archère courageuse vainquent un dragon et gouvernent le royaume ensemble.
- Le dragon qui terrorisait un beau royaume est abattu par une archère qui devient la femme du roi.
Execution complete in 9635 ms!
======== Planning - Create and Execute Book Creation Plan  ========
Original plan:
<goal>
Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'
</goal>
<plan>
  <function.WriterSkill.NovelOutline input="A group of kids in a club called 'The Thinking Caps' solve mysteries and puzzles using their creativity and logic." chapterCount="3" endMarker="***" setContextVariable="OUTLINE" />
  <function.planning.BucketOutputs input="$OUTLINE" bucketCount="3" bucketLabelPrefix="CHAPTER" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_1" theme="Mystery" chapterIndex="1" appendToResult="RESULT__CHAPTER_1" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_2" theme="Mystery" previousChapter="$CHAPTER_1" chapterIndex="2" appendToResult="RESULT__CHAPTER_2" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_3" theme="Mystery" previousChapter="$CHAPTER_2" chapterIndex="3" appendToResult="RESULT__CHAPTER_3" />
</plan>
Step 1 - Execution results:
<goal>
Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'
</goal><plan>
  <function.planning.BucketOutputs input="$OUTLINE" bucketCount="3" bucketLabelPrefix="CHAPTER" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_1" theme="Mystery" chapterIndex="1" appendToResult="RESULT__CHAPTER_1" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_2" theme="Mystery" previousChapter="$CHAPTER_1" chapterIndex="2" appendToResult="RESULT__CHAPTER_2" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_3" theme="Mystery" previousChapter="$CHAPTER_2" chapterIndex="3" appendToResult="RESULT__CHAPTER_3" />
</plan>
Step 2 - Execution results:
<goal>
Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'
</goal><plan>
  <function.WriterSkill.NovelChapter input="$CHAPTER_1" theme="Mystery" chapterIndex="1" appendToResult="RESULT__CHAPTER_1" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_2" theme="Mystery" previousChapter="$CHAPTER_1" chapterIndex="2" appendToResult="RESULT__CHAPTER_2" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_3" theme="Mystery" previousChapter="$CHAPTER_2" chapterIndex="3" appendToResult="RESULT__CHAPTER_3" />
</plan>
warn: object[0]
      Variable `$previousChapter` not found
Step 3 - Execution results:
<goal>
Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'
</goal><plan>
  <function.WriterSkill.NovelChapter input="$CHAPTER_2" theme="Mystery" previousChapter="$CHAPTER_1" chapterIndex="2" appendToResult="RESULT__CHAPTER_2" />
  <function.WriterSkill.NovelChapter input="$CHAPTER_3" theme="Mystery" previousChapter="$CHAPTER_2" chapterIndex="3" appendToResult="RESULT__CHAPTER_3" />
</plan>
Step 4 - Execution results:
<goal>
Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'
</goal><plan>
  <function.WriterSkill.NovelChapter input="$CHAPTER_3" theme="Mystery" previousChapter="$CHAPTER_2" chapterIndex="3" appendToResult="RESULT__CHAPTER_3" />
</plan>
Step 5 - Execution results:
<goal>
Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'
</goal><plan>
</plan>
Step 5 - COMPLETE!


RESULT__CHAPTER_1

The Thinking Caps were sitting in their usual spot in the library, surrounded by books, papers, and gadgets. They were busy studying and preparing for the upcoming trivia contest, which was only a few days away.

"Okay, team, let's review what we've learned so far," Max said, holding a clipboard and a pen. He was wearing a blue cap with a light bulb logo, which matched his bright eyes and blond hair. "Lily, what is the capital of Peru?"

"Lima," Lily answered without hesitation. She was wearing a purple cap with a paintbrush logo, which complemented her long brown hair and artistic flair. She was also holding a sketchbook and a pencil, where she had drawn a map of South America and some of its landmarks.

"Correct. Sam, what is the name of the device that measures atmospheric pressure?"

"A barometer," Sam replied confidently. He was wearing a green cap with a wrench logo, which suited his short black hair and inventive mind. He was also holding a small gadget that he had made out of spare parts, which he claimed could measure the temperature, humidity, and wind speed.

"Correct. Mia, what is the term for a word that sounds the same as another word but has a different meaning and spelling?"

"A homophone," Mia said with a smile. She was wearing a red cap with a pen logo, which matched her curly red hair and journalistic spirit. She was also holding a notebook and a recorder, where she had written down some trivia questions and recorded some interviews with the school staff and students.

"Correct. You guys are amazing. We're going to ace this contest for sure," Max said, giving them a thumbs up. "We've covered geography, science, and language. What's next?"

"How about history?" Lily suggested. "That's always fun."

"Good idea. Let's see, who can tell me who was the first president of the United States?" Max asked, looking at his clipboard.

"George Washington," the four friends said in unison.

"Too easy. How about who was the first president of France?" Max asked, raising the difficulty level.

"Napoleon Bonaparte," Sam said, raising his hand.

"Wrong. He was the first emperor of France, not the president. The first president was Louis-Napoleon Bonaparte, his nephew," Mia corrected him, showing off her knowledge.

"Wow, Mia, you're a history buff. How do you know all this stuff?" Sam asked, impressed.

"I read a lot of books and magazines. And I watch a lot of documentaries and podcasts. History is fascinating. It's like a giant mystery waiting to be solved," Mia explained, her eyes sparkling.

"I agree. History is full of clues and secrets. And speaking of mysteries, do you guys know what's the biggest mystery in our school right now?" Max asked, changing the topic.

"What?" the others asked, curious.

"The case of the missing mascot," Max said, lowering his voice and looking around. "Have you heard about it?"

"Of course we have. Everyone has. It's been the talk of the school for the past week," Lily said, nodding.

"For those who don't know, our school mascot, Hootie the owl, has been stolen from the principal's office. Hootie is a stuffed animal that has been with the school for over 50 years. He's not only a symbol of our school spirit, but also a lucky charm for us, the Thinking Caps. We always bring him along to our competitions, and we always win," Max explained, sounding proud and sad at the same time.

"Who would do such a thing? Who would steal Hootie?" Sam asked, shaking his head.

"That's the mystery. No one knows who did it, or why, or how. The principal's office was locked and alarmed, and there was no sign of forced entry or exit. The only clue was a note that was left on the principal's desk. It said: 'Hootie is gone. You'll never see him again. Good luck with the trivia contest. You'll need it.' And it was signed with a question mark," Max said, showing them a copy of the note that he had obtained from Mia.

"That's creepy. And mean. And rude. And unfair. And..." Lily said, running out of adjectives.

"And challenging," Max said, interrupting her. "Don't you see? This is a challenge for us, the Thinking Caps. Someone is trying to mess with us, to sabotage our chances of winning the contest. Someone who thinks they can outsmart us, outwit us, outplay us. Someone who wants to see us fail."

"Who could it be? Who hates us that much?" Sam asked, looking around suspiciously.

"It could be anyone. It could be the chess club, our main rivals in the contest. They're always jealous of our skills and achievements. They're always trying to beat us and prove that they're smarter than us," Max said, narrowing his eyes.

"Or it could be the class clown, the one who's always pulling pranks and jokes on everyone. He's always looking for a laugh and a thrill. He's always trying to get attention and cause trouble," Lily said, frowning.

"Or it could be the new kid, the one who's always quiet and mysterious. He's always alone and secretive. He's always hiding something and watching everything," Mia said, pointing at a corner where a boy with dark hair and glasses was sitting by himself, reading a book.

"Or it could be someone else, someone we don't know, someone we don't expect, someone who's hiding in plain sight," Sam said, widening his eyes.

"Whoever it is, we're not going to let them get away with it. We're not going to let them steal our mascot and our glory. We're not going to let them win. We're going to find Hootie and bring him back. We're going to solve this mystery and win this contest. We're going to show them who the real Thinking Caps are," Max said, raising his voice and his fist.

"Yeah!" the others said, joining him.

"Are you with me, team?" Max asked, looking at them.

"Always," they said, nodding.

"Then let's do this. Let's crack this case. Let's find the missing mascot. Let's go, Thinking Caps!" Max said, leading them out of the library.

"Let's go, Thinking Caps!" they repeated, following him.

And so, the adventure began. The Case of the Missing Mascot. The first mystery of the Thinking Caps. The first challenge of their lives. The first chapter of their story.

RESULT__CHAPTER_2

The Thinking Caps were sitting at their usual table in the library, surrounded by books, papers, and laptops. They were preparing for their next trivia contest, which was only a week away. They had already won the first round, thanks to their knowledge and teamwork. They were determined to win the second round, too, and make it to the finals.

"Okay, team, let's review what we've learned so far," Max said, holding a clipboard and a pen. He was the leader and the brains of the group, and he always had a plan. "The topic for the second round is history. We've covered ancient civilizations, medieval times, and the American Revolution. What's next?"

"How about the French Revolution?" Lily suggested, raising her hand. She was the artist and the heart of the group, and she loved to draw and paint. She had a sketchbook and a pencil in front of her, where she had doodled some scenes from the history books. "It's one of my favorite periods. There was so much drama, romance, and art."

"Good idea, Lily," Max said, nodding. "The French Revolution was a pivotal moment in world history. It changed the course of politics, culture, and society. There are a lot of facts and dates to remember, though. We'll need to study hard."

"I've got that covered," Sam said, smiling. He was the inventor and the hands of the group, and he liked to build and tinker with gadgets and machines. He had a laptop and a pair of headphones on the table, where he had created a quiz app to help them memorize the information. "I've programmed a fun and interactive way to learn about the French Revolution. It's called 'Guillotine or Not'. You have to answer questions correctly, or else you lose your head."

"Sounds gruesome, but effective," Mia said, chuckling. She was the journalist and the voice of the group, and she enjoyed writing and reporting. She had a notebook and a pen on the table, where she had written some catchy headlines and summaries of the historical events. "I've also done some research on the French Revolution. Did you know that there was a secret society of revolutionaries called the Jacobins? They were behind some of the most radical and violent actions of the revolution, such as the Reign of Terror."

"Wow, that's fascinating," Max said, impressed. "The French Revolution was full of secrets and mysteries. Just like our library."

The group looked around the library, which was their favorite place to hang out and study. The library was a large and old building, with high ceilings, wooden floors, and stained glass windows. It had thousands of books, ranging from fiction to non-fiction, from classics to comics. It also had a cozy reading area, a computer lab, and a media center. The library was a treasure trove of knowledge and entertainment for the Thinking Caps.

But lately, the library had also become a source of mystery and intrigue for the group. They had noticed that something strange was going on there. Books were disappearing from the shelves, without any record of being checked out or returned. Strange noises were heard at night, such as footsteps, whispers, and thuds. And a ghostly figure was seen roaming the aisles, wearing a long cloak and a hood.

The group was intrigued by the mystery and decided to investigate. They had asked the librarian, Mrs. Jones, about the strange occurrences, but she had dismissed them as rumors and pranks. She had told them that the library was perfectly safe and normal, and that they should focus on their studies and not on their imaginations.

But the group was not convinced. They had a feeling that there was more to the story than Mrs. Jones was letting on. They had done some digging and found out that the library had a rich and mysterious history, dating back to the founding of the town. The library was once the home of a wealthy and eccentric family, the Van Dorens, who collected rare and valuable books from all over the world. Some of these books were rumored to contain secrets, spells, and curses.

The group had also learned that the library was in danger of being closed down due to budget cuts and low attendance. The town council had decided that the library was too old and too expensive to maintain, and that it was not serving the needs of the community. They had proposed to sell the building and the books, and use the money to fund other projects. The library had only a few months left to prove its worth and attract more visitors, or else it would be gone forever.

The group was saddened and outraged by this news. They loved the library and wanted to save it. They also wanted to solve the mystery of the hauntings and find out the truth behind the library's secrets. They had a hunch that the two things were connected, and that the ghost was trying to tell them something.

They had come up with a plan to spend a night at the library, hoping to catch the ghost and find out what it wanted. They had convinced Mrs. Jones to let them stay after hours, under the pretext of doing a special project for the trivia contest. They had brought along their gadgets, tools, and books to help them. They had also brought their school mascot, a stuffed owl named Hootie, who was their lucky charm and their companion.

They were ready to face the challenge and the adventure that awaited them. They were the Thinking Caps, and they loved to solve mysteries and puzzles using their creativity and logic.

"Are you guys ready?" Max asked, looking at his friends.

"Ready as ever," Lily said, smiling.

"Let's do this," Sam said, nodding.

"Bring it on," Mia said, grinning.

They packed their bags and put on their jackets. They grabbed Hootie and headed to the door. They looked at the clock. It was 9 p.m. The library was officially closed. The night had begun.

RESULT__CHAPTER_3

The Case of the Secret Treasure

The Thinking Caps were in the library, browsing through the books and magazines, when they saw something that caught their eye. It was a newspaper article about the old town hall, which was being renovated and turned into a museum. The article said that the town hall was built in the late 1800s by the town's founder, John B. Smith, who was a famous explorer and adventurer. He traveled the world and collected priceless artifacts and jewels, which he brought back to his hometown and displayed in his mansion. The mansion was later donated to the town and became the town hall.

The article also said that there was a rumor that Smith had hidden a secret treasure somewhere in the town, before he died in a mysterious accident. The treasure was said to be worth millions of dollars, and contained rare and exotic items from his travels. The rumor had sparked the interest of many treasure hunters and adventurers, who had searched for the treasure for decades, but none of them had ever found it.

The Thinking Caps were fascinated by the article and the story of the treasure. They loved mysteries and challenges, and they wondered if they could find the treasure themselves. They decided to do some research on Smith and his travels, and see if they could find any clues or hints about the treasure.

They went to the librarian, Mrs. Jones, and asked her if she had any books or documents about Smith and his adventures. Mrs. Jones smiled and said that she did have some, but they were not in the main library. They were in a special section of the library, called the Smith Collection. The Smith Collection was a room that contained all the books, papers, and artifacts that Smith had donated to the library, along with his mansion. The room was locked and only accessible to authorized people, such as the librarian and the town historian.

Mrs. Jones said that she would let the Thinking Caps see the Smith Collection, as she knew that they were smart and curious kids who loved to learn. She said that she would give them a tour of the room and show them some of the items that Smith had collected. She said that they had to be careful and respectful, as the items were very old and valuable. She also said that they had to be quiet and discreet, as the room was not open to the public, and some people might not like them snooping around.

The Thinking Caps agreed to follow Mrs. Jones' rules and thanked her for the opportunity. They followed her to the back of the library, where she took out a key and opened a door that led to a staircase. They climbed the stairs and entered the Smith Collection.

The room was dimly lit and dusty, but full of wonders. The walls were lined with shelves that held books of all kinds and sizes, some of them leather-bound and gold-embossed, some of them worn and torn. The books covered topics such as history, geography, mythology, science, and art. There were also maps, charts, journals, and letters that Smith had written or received during his travels. The room also had cabinets and cases that displayed various artifacts and jewels that Smith had collected. There were statues, vases, coins, medals, weapons, tools, and ornaments that came from different countries and cultures. There were also gems, pearls, diamonds, and rubies that sparkled and glittered in the light.

The Thinking Caps were amazed and awed by the sight. They felt like they had entered a treasure trove, a museum, and a library all in one. They wanted to look at everything and learn more about Smith and his adventures. They asked Mrs. Jones if they could browse through the books and documents, and she said that they could, as long as they were careful and gentle. She said that she would stay with them and answer any questions they had. She also said that they had to be back in the main library before it closed, as she had to lock the room and return the key.

The Thinking Caps nodded and thanked her again. They split up and went to different sections of the room, where they picked up books and papers that interested them. They read, studied, and examined the items, and shared their findings with each other. They learned a lot about Smith and his travels, and they also learned a lot about the world and its history.

They also found something that they did not expect to find. It was a clue that led them to the secret treasure. The clue was a map that showed the location of a hidden chamber under the old town hall, where the treasure was buried. The map was hidden inside a book that looked like a normal history book, but was actually a hollowed-out book that contained a secret compartment. The book was titled "The History of the World", and it was written by Smith himself. The Thinking Caps found the book on a shelf that was labeled "Smith's Personal Collection".

The map was drawn on a piece of parchment, and it had a note attached to it. The note said:

To whoever finds this map,

You have proven yourself to be a worthy and clever seeker, by finding this hidden book and opening its secret compartment. You have also shown yourself to be a lover of knowledge and adventure, by reading and learning from my books and papers. I congratulate you and commend you for your curiosity and intelligence.

You are now one step closer to finding my greatest treasure, the one that I have hidden under the old town hall, where I once lived and worked. The treasure is a collection of the most rare and valuable items that I have gathered from my travels around the world. It is a testament to my life and legacy, and a gift to my beloved hometown.

However, finding the treasure will not be easy. You will have to follow the map and find the entrance to the hidden chamber, which is well concealed and guarded. You will also have to solve the puzzles and riddles that I have left for you, as a way of testing your intelligence and courage. The puzzles and riddles involve various subjects and skills, such as history, geography, math, science, and art. You will have to use your creativity and logic to overcome the obstacles and dangers that await you.

If you succeed, you will be rewarded with the treasure and the honor of being the first and only person to find it. If you fail, you will face the consequences of your failure, which may include death or worse. You have been warned.

The choice is yours. Do you have what it takes to find the treasure and claim it as your own? Or do you lack the courage and the wisdom to do so? Only you can decide.

Good luck, and may the spirit of adventure guide you.

John B. Smith

The Thinking Caps were stunned and excited by the note and the map. They could not believe that they had found a clue to the secret treasure, and that they had a chance to find it. They looked at each other and nodded. They knew what they wanted to do. They wanted to follow the map and find the treasure. They wanted to have the adventure of a lifetime. They wanted to make history.

They quickly put the map and the note back in the book and closed it. They returned the book to the shelf and acted as if nothing had happened. They thanked Mrs. Jones for the tour and said that they had to go. They left the Smith Collection and the library, and headed to their meeting place, a nearby park. There, they discussed their plan and prepared for their quest.

They knew that they had to be careful and discreet, as they were not the only ones who were interested in the treasure. They had to deal with a greedy and ruthless treasure hunter who was also after the prize. The treasure hunter was a man named Max Stone, who was a notorious and infamous adventurer. He was known for his cunning and cruelty, and for his obsession with finding and stealing treasures. He had heard about the rumor of Smith's treasure, and he had come to town to look for it. He had been spying on the library and the town hall, hoping to find a clue or a hint. He had also been following and harassing the Thinking Caps, trying to intimidate and discourage them from their investigation.

The Thinking Caps had to use their creativity and logic to overcome the obstacles and dangers that Stone set for them. They also had to solve the puzzles and riddles that Smith left for them, as a way of testing their intelligence and courage. The puzzles and riddles involved various subjects and skills, such as history, geography, math, science, and art.

They also had to use their gadgets, tools, and books to help them. They had a backpack that contained a flashlight, a magnifying glass, a compass, a calculator, a notebook, a pen, a camera, a phone, and a laptop. They also had a book that contained information and facts about Smith and his travels, which they had borrowed from the library. They called it the Smith Book, and they used it as a reference and a guide.

They were ready for their biggest and most exciting adventure yet. They were ready to follow the map and find the treasure. They were ready to face the challenges and the dangers. They were ready to become the Thinking Caps.
Execution complete in 317132 ms!

*/
// ReSharper restore CommentTypo
