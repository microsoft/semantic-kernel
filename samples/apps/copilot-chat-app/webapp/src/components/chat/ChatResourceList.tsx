// Copyright (c) Microsoft. All rights reserved.

import {
    Table,
    TableBody,
    TableCell,
    TableCellLayout,
    TableColumnDefinition,
    TableColumnId,
    TableHeader,
    TableHeaderCell,
    TableHeaderCellProps,
    TableRow,
    createTableColumn,
    makeStyles,
    shorthands,
    tokens,
    useTableFeatures,
    useTableSort,
} from '@fluentui/react-components';
import { DocumentPdfRegular, DocumentTextRegular } from '@fluentui/react-icons';
import * as React from 'react';
import { ChatMemorySource } from '../../libs/models/ChatMemorySource';
import { useChat } from '../../libs/useChat';
import { SharedStyles } from '../../styles';
import { timestampToDateString } from '../utils/TextUtils';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        ...SharedStyles.scroll,
    },
    table: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    tableHeader: {
        fontWeight: tokens.fontSizeBase600,
    },
});

interface ChatResourceListProps {
    chatId: string;
}

export const ChatResourceList: React.FC<ChatResourceListProps> = ({ chatId }) => {
    const classes = useClasses();
    const chat = useChat();
    const [resources, setResources] = React.useState<ChatMemorySource[]>([]);

    React.useEffect(() => {
        chat.getChatMemorySources(chatId).then((sources) => {
            setResources(sources);
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [chatId]);

    const { columns, rows } = useTable(resources);
    return (
        <div className={classes.root}>
            <Table aria-label="External resource table" className={classes.table}>
                <TableHeader>
                    <TableRow>{columns.map((column) => column.renderHeaderCell())}</TableRow>
                </TableHeader>
                <TableBody>
                    {rows.map((item) => (
                        <TableRow key={item.id}>{columns.map((column) => column.renderCell(item))}</TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
};

interface TableItem {
    id: string;
    name: {
        label: string;
        icon: JSX.Element;
        url?: string;
    };
    createdOn: {
        label: string;
        timestamp: number;
    };
}

function useTable(resources: ChatMemorySource[]) {
    const headerSortProps = (columnId: TableColumnId): TableHeaderCellProps => ({
        onClick: (e: React.MouseEvent) => {
            toggleColumnSort(e, columnId);
        },
        sortDirection: getSortDirection(columnId),
    });

    const columns: TableColumnDefinition<TableItem>[] = [
        createTableColumn<TableItem>({
            columnId: 'name',
            renderHeaderCell: () => <TableHeaderCell {...headerSortProps('name')}>Name</TableHeaderCell>,
            renderCell: (item) => (
                <TableCell>
                    <TableCellLayout media={item.name.icon}>
                        <a href={item.name.url}>{item.name.label}</a>
                    </TableCellLayout>
                </TableCell>
            ),
            compare: (a, b) => {
                const comparison = a.name.label.localeCompare(b.name.label);
                return getSortDirection('name') === 'ascending' ? comparison : comparison * -1;
            },
        }),
        createTableColumn<TableItem>({
            columnId: 'createdOn',
            renderHeaderCell: () => <TableHeaderCell {...headerSortProps('createdOn')}>Created on</TableHeaderCell>,
            renderCell: (item) => (
                <TableCell title={new Date(item.createdOn.timestamp).toLocaleString()}>
                    {item.createdOn.label}
                </TableCell>
            ),
            compare: (a, b) => {
                const comparison = a.createdOn.timestamp > b.createdOn.timestamp ? 1 : -1;
                return getSortDirection('createdOn') === 'ascending' ? comparison : comparison * -1;
            },
        }),
    ];

    const items = resources.map((item) => ({
        id: item.id,
        name: {
            label: item.name,
            icon: getFileIconByFileExtension(item.name),
            url: item.hyperlink,
        },
        createdOn: {
            label: timestampToDateString(item.createdOn),
            timestamp: item.createdOn,
        },
    }));

    const {
        sort: { getSortDirection, toggleColumnSort, sortColumn },
    } = useTableFeatures(
        {
            columns,
            items,
        },
        [
            useTableSort({
                defaultSortState: { sortColumn: 'name', sortDirection: 'ascending' },
            }),
        ],
    );

    if (sortColumn) {
        items.sort((a, b) => {
            const compare = columns.find((column) => column.columnId === sortColumn)?.compare;
            return compare?.(a, b) ?? 0;
        });
    }

    return { columns, rows: items };
}

function getFileIconByFileExtension(fileName: string) {
    const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.') + 1);
    if (extension === 'pdf') {
        return <DocumentPdfRegular />;
    }
    return <DocumentTextRegular />;
}
