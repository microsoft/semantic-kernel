// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessFramework.Aspire.ProcessOrchestrator;
using ProcessFramework.Aspire.ProcessOrchestrator.Models;
using ProcessFramework.Aspire.ProcessOrchestrator.Steps;

var builder = WebApplication.CreateBuilder(args);

AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

builder.AddServiceDefaults();
builder.Services.AddHttpClient<TranslatorAgentHttpClient>(client => { client.BaseAddress = new("https+http://translatoragent"); });
builder.Services.AddHttpClient<SummaryAgentHttpClient>(client => { client.BaseAddress = new("https+http://summaryagent"); });
builder.Services.AddSingleton(builder =>
{
    var kernelBuilder = Kernel.CreateBuilder();

    kernelBuilder.Services.AddSingleton(builder.GetRequiredService<TranslatorAgentHttpClient>());
    kernelBuilder.Services.AddSingleton(builder.GetRequiredService<SummaryAgentHttpClient>());

    return kernelBuilder.Build();
});

var app = builder.Build();

app.UseHttpsRedirection();

app.MapGet("/api/processdoc", async (Kernel kernel) =>
{
    var processBuilder = new ProcessBuilder("ProcessDocument");
    var translateDocumentStep = processBuilder.AddStepFromType<TranslateStep>();
    var summarizeDocumentStep = processBuilder.AddStepFromType<SummarizeStep>();

    processBuilder
        .OnInputEvent(ProcessEvents.TranslateDocument)
        .SendEventTo(new(translateDocumentStep, TranslateStep.Functions.Translate, parameterName: "textToTranslate"));

    translateDocumentStep
        .OnEvent(ProcessEvents.DocumentTranslated)
        .SendEventTo(new(summarizeDocumentStep, SummarizeStep.Functions.Summarize, parameterName: "textToSummarize"));

    summarizeDocumentStep
        .OnEvent(ProcessEvents.DocumentSummarized)
        .StopProcess();

    var process = processBuilder.Build();
    await using var runningProcess = await process.StartAsync(
        kernel,
        new KernelProcessEvent { Id = ProcessEvents.TranslateDocument, Data = "COME I FORNITORI INFLUENZANO I TUOI COSTI Quando scegli un piano di assicurazione sanitaria, uno dei fattori più importanti da considerare è la rete di fornitori in convenzione disponibili con il piano. Northwind Standard offre un'ampia varietà di fornitori in convenzione, tra cui medici di base, specialisti, ospedali e farmacie. Questo ti permette di scegliere un fornitore comodo per te e la tua famiglia, contribuendo al contempo a mantenere bassi i tuoi costi. Se scegli un fornitore in convenzione con il tuo piano, pagherai generalmente copay e franchigie più basse rispetto a un fornitore fuori rete. Inoltre, molti servizi, come l'assistenza preventiva, possono essere coperti senza alcun costo aggiuntivo se ricevuti da un fornitore in convenzione. È importante notare, tuttavia, che Northwind Standard non copre i servizi di emergenza, l'assistenza per la salute mentale e l'abuso di sostanze, né i servizi fuori rete. Questo significa che potresti dover pagare di tasca tua per questi servizi se ricevuti da un fornitore fuori rete. Quando scegli un fornitore in convenzione, ci sono alcuni suggerimenti da tenere a mente. Verifica che il fornitore sia in convenzione con il tuo piano. Puoi confermarlo chiamando l'ufficio del fornitore e chiedendo se è in rete con Northwind Standard. Puoi anche utilizzare lo strumento di ricerca fornitori sul sito web di Northwind Health per verificare la copertura. Assicurati che il fornitore stia accettando nuovi pazienti. Alcuni fornitori potrebbero essere in convenzione ma non accettare nuovi pazienti. Considera la posizione del fornitore. Se il fornitore è troppo lontano, potrebbe essere difficile raggiungere gli appuntamenti. Valuta gli orari dell'ufficio del fornitore. Se lavori durante il giorno, potresti aver bisogno di trovare un fornitore con orari serali o nel fine settimana. Scegliere un fornitore in convenzione può aiutarti a risparmiare sui costi sanitari. Seguendo i suggerimenti sopra e facendo ricerche sulle opzioni disponibili, puoi trovare un fornitore conveniente, accessibile e in rete con il tuo piano Northwind Standard." }
    );

    return Results.Ok("Process completed successfully");
});

app.MapDefaultEndpoints();

app.Run();
