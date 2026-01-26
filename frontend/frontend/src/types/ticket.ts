export type Ticket = {
    id: string;
    created_at: string;
    description: string;
    category: string | null;
    sentiment: string | null;
    processed: boolean;
};
