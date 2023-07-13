// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Services.Storage.Queue;

// See https://medium.com/@a.lyskawa/the-hitchhiker-guide-to-asynchronous-events-in-c-e9840109fb53
public delegate Task AsyncMessageHandler<in T>(object sender, T e);
