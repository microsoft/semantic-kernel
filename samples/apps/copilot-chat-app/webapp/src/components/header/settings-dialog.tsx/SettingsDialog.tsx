// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Divider,
    Label,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { TokenUsage } from '../../shared/TokenUsage';
import { useDialogClasses } from '../../shared/styles';
import { SettingSection } from './SettingSection';

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('scroll'),
        display: 'flex',
        flexDirection: 'column',
        height: '650px',
    },
    footer: {
        paddingTop: tokens.spacingVerticalL,
    },
    paddingLeft: {
        paddingLeft: tokens.spacingHorizontalMNudge,
    },
});

interface ISettingsDialogProps {
    open: boolean;
    closeDialog: () => void;
}

export const SettingsDialog: React.FC<ISettingsDialogProps> = ({ open, closeDialog }) => {
    const classes = useClasses();
    const dialogClasses = useDialogClasses();
    const { settings, tokenUsage } = useAppSelector((state: RootState) => state.app);

    return (
        <Dialog
            open={open}
            onOpenChange={(_ev: any, data: DialogOpenChangeData) => {
                if (!data.open) closeDialog();
            }}
        >
            <DialogSurface>
                <DialogBody className={classes.root}>
                    <DialogTitle>Settings</DialogTitle>
                    <DialogContent>
                        <TokenUsage
                            sessionTotal
                            promptUsage={tokenUsage.prompt}
                            dependencyUsage={tokenUsage.dependency}
                        />
                        <Accordion collapsible multiple defaultOpenItems={['basic', 'advanced']}>
                            <AccordionItem value="basic">
                                <AccordionHeader expandIconPosition="end">
                                    <h3>Basic</h3>
                                </AccordionHeader>
                                <AccordionPanel>
                                    <SettingSection key={settings[0].title} setting={settings[0]} contentOnly />
                                </AccordionPanel>
                            </AccordionItem>
                            <Divider />
                            <AccordionItem value="advanced">
                                <AccordionHeader expandIconPosition="end">
                                    <h3>Advanced</h3>
                                </AccordionHeader>
                                <AccordionPanel>
                                    {settings.slice(1).map((setting) => {
                                        return <SettingSection key={setting.title} setting={setting} />;
                                    })}
                                </AccordionPanel>
                            </AccordionItem>
                        </Accordion>
                    </DialogContent>
                </DialogBody>
                <DialogActions position="start" className={dialogClasses.footer}>
                    <Label size="small" color="brand" className={classes.footer}>
                        Join the Semantic Kernel open source community!{' '}
                        <a href="https://aka.ms/semantic-kernel" target="_blank" rel="noreferrer">
                            Learn More
                        </a>
                    </Label>
                    <DialogTrigger disableButtonEnhancement>
                        <Button appearance="secondary">Close</Button>
                    </DialogTrigger>
                </DialogActions>
            </DialogSurface>
        </Dialog>
    );
};
