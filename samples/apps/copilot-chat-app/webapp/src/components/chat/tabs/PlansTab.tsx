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
    tokens,
    useTableFeatures,
    useTableSort,
} from '@fluentui/react-components';
import { ChatMessageType, IChatMessage } from '../../../libs/models/ChatMessage';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { TokenUsages } from '../../../redux/features/app/AppState';
import { timestampToDateString } from '../../utils/TextUtils';
import { PlanJsonViewer } from '../plan-viewer/PlanJsonViewer';
import { TabView } from './TabView';

const useClasses = makeStyles({
    table: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    tableHeader: {
        fontWeight: tokens.fontSizeBase600,
    },
});

interface TableItem {
    index: number;
    ask: string;
    createdOn: {
        label: string;
        timestamp: number;
    };
    tokens: number;
    message: IChatMessage;
}

export const PlansTab: React.FC = () => {
    const classes = useClasses();

    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const chatMessages = conversations[selectedId].messages;
    const planMessages = chatMessages.filter((message) => message.type === ChatMessageType.Plan);

    const { columns, rows } = useTable(planMessages);
    return (
        <TabView title="Plans" learnMoreDescription="custom plans" learnMoreLink="https://aka.ms/sk-docs-planner">
            <Table aria-label="Processes plan table" className={classes.table}>
                <TableHeader>
                    <TableRow>{columns.map((column) => column.renderHeaderCell())}</TableRow>
                </TableHeader>
                <TableBody>
                    {rows.map((item) => (
                        <TableRow key={item.ask}>{columns.map((column) => column.renderCell(item))}</TableRow>
                    ))}
                </TableBody>
            </Table>
        </TabView>
    );
};

function useTable(planMessages: IChatMessage[]) {
    const headerSortProps = (columnId: TableColumnId): TableHeaderCellProps => ({
        onClick: (e: React.MouseEvent) => {
            toggleColumnSort(e, columnId);
        },
        sortDirection: getSortDirection(columnId),
    });

    const columns: Array<TableColumnDefinition<TableItem>> = [
        createTableColumn<TableItem>({
            columnId: 'ask',
            renderHeaderCell: () => (
                <TableHeaderCell key="ask" {...headerSortProps('ask')}>
                    Ask
                </TableHeaderCell>
            ),
            renderCell: (item) => (
                <TableCell key={`plan-${item.index}`}>
                    <TableCellLayout>
                        <PlanJsonViewer
                            goal={item.ask}
                            tokenUsage={item.message.tokenUsage as TokenUsages}
                            json={item.message.content}
                        />
                    </TableCellLayout>
                </TableCell>
            ),
            compare: (a, b) => {
                const comparison = a.ask.localeCompare(b.ask);
                return getSortDirection('name') === 'ascending' ? comparison : comparison * -1;
            },
        }),
        createTableColumn<TableItem>({
            columnId: 'createdOn',
            renderHeaderCell: () => (
                <TableHeaderCell key="createdOn" {...headerSortProps('createdOn')}>
                    Created on
                </TableHeaderCell>
            ),
            renderCell: (item) => (
                <TableCell key={item.createdOn.timestamp} title={new Date(item.createdOn.timestamp).toLocaleString()}>
                    {item.createdOn.label}
                </TableCell>
            ),
            compare: (a, b) => {
                const comparison = a.createdOn.timestamp > b.createdOn.timestamp ? 1 : -1;
                return getSortDirection('createdOn') === 'ascending' ? comparison : comparison * -1;
            },
        }),
        createTableColumn<TableItem>({
            columnId: 'tokenCounts',
            renderHeaderCell: () => (
                <TableHeaderCell key="tokenCounts" {...headerSortProps('tokenCounts')}>
                    Token Count
                </TableHeaderCell>
            ),
            renderCell: (item) => <TableCell key={`plan-${item.index}-tokens`}>{item.tokens}</TableCell>,
            compare: (a, b) => {
                const comparison = a.tokens - b.tokens;
                return getSortDirection('tokenCounts') === 'ascending' ? comparison : comparison * -1;
            },
        }),
    ];

    /*
    eslint-disable 
        @typescript-eslint/no-unsafe-assignment,
        @typescript-eslint/no-unsafe-member-access,
        @typescript-eslint/no-unsafe-call,
    */
    const items = planMessages.map((message, index) => {
        const plan = JSON.parse(message.content);
        const planDescription = plan.proposedPlan.description as string;
        const planAsk =
            planDescription
                .split('\n')
                .find((line: string) => line.startsWith('INPUT:'))
                ?.replace('INPUT:', '')
                .trim() ?? 'N/A';
        return {
            index: index,
            ask: planAsk,
            createdOn: {
                label: timestampToDateString(message.timestamp),
                timestamp: message.timestamp,
            },
            tokens: message.tokenUsage?.planExecution ?? 0,
            message: message,
        };
    });

    const {
        sort: { getSortDirection, toggleColumnSort, sortColumn },
    } = useTableFeatures(
        {
            columns,
            items,
        },
        [
            useTableSort({
                defaultSortState: { sortColumn: 'createdOn', sortDirection: 'descending' },
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
