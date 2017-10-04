// For compile-time type checking and code completion

export interface Investment {
    amount: number;
    campaign_id: number;
    campaign_user_id: string;
    contract_id: string;
    duration: number;
    id: number;
    user_id: string;
    interest_rate: number;
    status: string;
    transfers: object[];
}