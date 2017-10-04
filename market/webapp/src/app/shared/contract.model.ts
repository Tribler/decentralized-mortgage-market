// For compile-time type checking and code completion

export interface Contract {
    confirmations: number;
    decoded: object;
    document: string;
    from_public_key: string;
    from_signature: string;
    id: string;
    previous_hash: string;
    time: number;
    to_public_key: string;
    to_signature: string;
}