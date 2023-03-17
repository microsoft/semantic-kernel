// Copyright (c) Microsoft. All rights reserved.

import React, { FC, useEffect } from 'react';
import { Body1, Title3, Spinner } from '@fluentui/react-components';

interface IData {
    uri: string;
    onFunctionFound: () => void;
}

const FunctionProbe: FC<IData> = ({ uri, onFunctionFound }) => {
    useEffect(() => {

        const fetchAsync = async () => {
            try {
                var result = await fetch(`${uri}/api/ping`);

                if (result.ok) {
                    onFunctionFound();
                }
            }
            catch {

            }
        }

        fetchAsync();
    });

    return (
        <div style={{ padding: 80, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Title3>Looking for your function</Title3>
            <Spinner />
            <Body1>This sample expects to find the Azure Function from <strong>samples/starter-api-azure-function</strong> running at <strong>{uri}</strong></Body1>
            <Body1>Run your Azure Function locally using <a href='https://learn.microsoft.com/azure/azure-functions/functions-develop-vs?tabs=in-process' target='_blank' rel='noreferrer'>Visual Studio</a>, <a href='https://learn.microsoft.com/azure/azure-functions/functions-develop-vs-code?tabs=csharp' target='_blank' rel='noreferrer'>Visual Studio Code</a> or from the command line using the <a href='https://github.com/Azure/azure-functions-core-tools' target='_blank' rel='noreferrer'>Azure Functions Core Tools</a></Body1>

        </div>
    );
}

export default FunctionProbe;
