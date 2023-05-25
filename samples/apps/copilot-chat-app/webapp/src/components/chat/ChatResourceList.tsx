// Copyright (c) Microsoft. All rights reserved.

import {
    TableBody,
    TableCell,
    TableRow,
    Table,
    TableHeader,
    TableHeaderCell,
    TableCellLayout,
    PresenceBadgeStatus,
    Avatar,
    shorthands,
    tokens,
    makeStyles,
} from '@fluentui/react-components';
import * as React from 'react';
import { DocumentPdfRegular } from '@fluentui/react-icons';
import { useChat } from '../../libs/useChat';
import { ChatMemorySource } from '../../libs/models/ChatMemorySource';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        backgroundColor: tokens.colorNeutralBackground1,
    },
    tableHeader: {
        fontWeight: '600',
    },
});

interface ChatResourceListProps {
    chatSessionId: string;
}

export const ChatResourceList: React.FC<ChatResourceListProps> = ({ chatSessionId }) => {
    const classes = useClasses();
    const chat = useChat();
    const [resources, setResources] = React.useState<ChatMemorySource[]>([]);

    React.useEffect(() => {
        chat.getChatMemorySources(chatSessionId).then((sources) => {
            setResources(sources);
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [chatSessionId]);

    const items = resources.map((item) => ({
        name: {
            label: item.name,
            icon: <DocumentPdfRegular /> /* TODO: change icon based on file extension */,
            url: item.hyperlink,
        },
        updatedOn: {
            label: new Date(item.updatedOn).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
            }),
            timestamp: item.updatedOn,
        },
        sharedBy: { label: item.sharedBy, status: 'available' },
    }));

    const columns = [
        { columnKey: 'name', label: 'Name' },
        { columnKey: 'updatedOn', label: 'Updated on' },
        { columnKey: 'sharedBy', label: 'Shared by' },
    ];

    return (
        <Table arial-label="External resource table" className={classes.root}>
            <TableHeader>
                <TableRow>
                    {columns.map((column) => (
                        <TableHeaderCell key={column.columnKey}>
                            <span className={classes.tableHeader}>{column.label}</span>
                        </TableHeaderCell>
                    ))}
                </TableRow>
            </TableHeader>
            <TableBody>
                {items.map((item) => (
                    <TableRow key={item.name.label}>
                        <TableCell>
                            <TableCellLayout media={item.name.icon}>
                                <a href={item.name.url}>{item.name.label}</a>
                            </TableCellLayout>
                        </TableCell>
                        <TableCell>{item.updatedOn.label}</TableCell>
                        <TableCell>
                            <TableCellLayout
                                media={
                                    <Avatar
                                        aria-label={item.sharedBy.label}
                                        name={item.sharedBy.label}
                                        badge={{
                                            status: item.sharedBy.status as PresenceBadgeStatus,
                                        }}
                                    />
                                }
                            >
                                {item.sharedBy.label}
                            </TableCellLayout>
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
};
