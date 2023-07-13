// Copyright (c) Microsoft. All rights reserved.

using System;

/* === 1 ===
 * Work in progress - Not ready
 */

// Example1_ImportWithMemoryClient.RunAsync().Wait();

/* === 2 ===
 * Define a pipeline, 100% C# handlers, and run it in this process.
 * Note: no web service required to run this.
 * The pipeline might use settings in appsettings.json, but explicitly
 * uses 'InProcessPipelineOrchestrator'.
 */

Example2_InProcessImport.RunAsync().Wait();
Console.WriteLine("============================");

/* === 3 ===
 * Upload some files to the web service, where the pipeline steps
 * are defined and run asynchronously using a distributed queue.
 *
 * Note: start the web service before running this
 */

Console.WriteLine("Make sure the semantic memory web service is running");
Console.WriteLine("Press a Enter to continue...");
Console.ReadLine();
Example3_MultiPartFormFilesUpload.RunAsync().Wait();
