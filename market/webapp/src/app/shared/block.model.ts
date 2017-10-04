// For compile-time type checking and code completion
import { Contract } from './contract.model';

export interface Block {
    contracts: Contract[];
    creator: string;
    creator_signature: string;
    height: number;
    id: string;
    merkle_root_hash: string;
    previous_hash: string;
    target_difficulty: string;
}