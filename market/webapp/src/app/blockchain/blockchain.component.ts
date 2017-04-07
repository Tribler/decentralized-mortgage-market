import { Component, OnInit } from '@angular/core';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'blockchain',
    templateUrl: 'blockchain.component.html',
    styleUrls: ['./blockchain.component.css']
})
export class BlockchainComponent implements OnInit {
    blocks = [];

    constructor(private _marketService: MarketService) { }

    ngOnInit() {
        this._marketService.getBlocks().subscribe(blocks => this.blocks = blocks);
    }
}
