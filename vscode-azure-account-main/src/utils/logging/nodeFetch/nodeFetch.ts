import fetch, { Request, RequestInfo, RequestInit, Response } from "node-fetch";
import { ext } from "../../../extensionVariables";
import { HttpLogger } from "../HttpLogger";
import { NodeFetchNormalizer } from "./NodeFetchNormalizer";

export async function fetchWithLogging(url: RequestInfo, init?: RequestInit): Promise<Response> {
    const nodeFetchLogger = new HttpLogger(ext.outputChannel, 'NodeFetch', new NodeFetchNormalizer());
    const request = new Request(url, init);
    nodeFetchLogger.logRequest(request);
    const response = await fetch(url, init);
    nodeFetchLogger.logResponse({ response, request, bodyAsText: await response.clone().text() });
    return response;
}