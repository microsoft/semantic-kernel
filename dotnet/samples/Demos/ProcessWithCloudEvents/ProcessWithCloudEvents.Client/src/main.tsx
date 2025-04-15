/*
 *   Copyright (c) 2025 Microsoft
 *   All rights reserved.
 */
import { createRoot } from "react-dom/client";
import { grpcDocService } from "./services/grpc/DocumentGenerationGrpcClient.ts";
import { FluentProvider, webLightTheme } from "@fluentui/react-components";
import "./index.css";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
    <FluentProvider theme={webLightTheme}>
        <App grpcDocClient={grpcDocService} />
    </FluentProvider>
);
