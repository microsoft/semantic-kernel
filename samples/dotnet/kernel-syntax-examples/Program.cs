// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

public static class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main(string[] args)
    {

        await Example43_TravelApp.RunAsync(args[0]);
        Console.WriteLine("== DONE ==");

    }
}
