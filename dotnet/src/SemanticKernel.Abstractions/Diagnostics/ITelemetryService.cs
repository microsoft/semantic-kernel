// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Diagnostics;
public interface ITelemetryService
{
    void TrackSkillEvent(string skillName, string functionName, bool success);
}
