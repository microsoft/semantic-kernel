// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Label,
    Link,
    Tooltip,
    makeStyles,
    shorthands,
} from '@fluentui/react-components';
import { Info16Regular } from '@fluentui/react-icons';
import React from 'react';
import { IChatMessage } from '../../../libs/models/ChatMessage';
import { TokenUsage } from '../../shared/TokenUsage';
import { useDialogClasses } from '../../shared/styles';

const useClasses = makeStyles({
    infoButton: {
        ...shorthands.padding(0),
        ...shorthands.margin(0),
        minWidth: 'auto',
        marginLeft: 'auto', // align to right
    },
});

interface IPromptDetailsProps {
    message: IChatMessage;
}

export const PromptDetails: React.FC<IPromptDetailsProps> = ({ message }) => {
    const classes = useClasses();
    const dialogClasses = useDialogClasses();

    return (
        <Dialog>
            <DialogTrigger disableButtonEnhancement>
                <Tooltip content={'Show prompt'} relationship="label">
                    <Button className={classes.infoButton} icon={<Info16Regular />} appearance="transparent" />
                </Tooltip>
            </DialogTrigger>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>Prompt</DialogTitle>
                    <DialogContent>
                        <TokenUsage
                            promptUsage={message.tokenUsage?.prompt ?? 0}
                            dependencyUsage={message.tokenUsage?.dependency ?? 0}
                        />
                        {!message.prompt
                            ? 'No prompt available. The response is either a plan proposal or a hard-coded response.'
                            : message.prompt
                                  .split('\n')
                                  .map((paragraph, idx) => <p key={`prompt-details-${idx}`}>{paragraph}</p>)}
                    </DialogContent>
                    <DialogActions position="start" className={dialogClasses.footer}>
                        <Label size="small" color="brand">
                            Want to learn more about prompts? Click{' '}
                            <Link href="https://aka.ms/sk-about-prompts" target="_blank" rel="noreferrer">
                                here
                            </Link>
                            .
                        </Label>
                        <DialogTrigger disableButtonEnhancement>
                            <Button appearance="secondary">Close</Button>
                        </DialogTrigger>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
