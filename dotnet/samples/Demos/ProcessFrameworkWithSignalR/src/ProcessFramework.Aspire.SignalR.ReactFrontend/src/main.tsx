/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { createRoot } from "react-dom/client";
import { SignalRDocumentationGenerationClient } from './services/signalr/documentGeneration.client';
import { ProcessFrameworkHttpClient } from './services/signalr/ProcessFrameworkClient';
import { FluentProvider, webLightTheme } from "@fluentui/react-components";
import "./index.css";
import App from "./App.tsx";

const signalRClient = new SignalRDocumentationGenerationClient();
const httpClient = new ProcessFrameworkHttpClient();

createRoot(document.getElementById("root")!).render(
    <FluentProvider theme={webLightTheme}>
        <App signalRClient={signalRClient} httpClient={httpClient} />
    </FluentProvider>
);
