// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Spinner } from '@fluentui/react-components';
import { CheckmarkCircle24Regular, PlayCircle24Regular } from '@fluentui/react-icons';
import { FC, useState } from 'react';

interface IData {
    taskDescription: string;
    runTask: () => Promise<void>;
}

const InteractionButton: FC<IData> = ({ taskDescription, runTask }) => {
    const [isBusy, setIsBusy] = useState<boolean>(false);
    const [canRunTask, setCanRunTask] = useState<boolean>(true);

    const run = async () => {
        setIsBusy(true);
        await runTask();
        setIsBusy(false);
        setCanRunTask(false);
    };

    return (
        <>
            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center' }}>
                <Button disabled={!canRunTask || isBusy} appearance="transparent" size="small" onClick={run}>
                    {!canRunTask ? (
                        <CheckmarkCircle24Regular primaryFill="green" filled={true} />
                    ) : (
                        <PlayCircle24Regular />
                    )}
                </Button>
                <Body1>{taskDescription}</Body1>
            </div>
            {isBusy ? <Spinner /> : null}
        </>
    );
};

export default InteractionButton;
