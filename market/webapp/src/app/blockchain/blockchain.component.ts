import { Component, OnInit } from '@angular/core';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'blockchain',
    template: `
        <pre [innerHtml]="blocks | prettyjson:2"></pre>
    `,
    styleUrls: ['./blockchain.component.css']
})
export class BlockchainComponent implements OnInit {
    blocks = [];

    constructor(private _marketService: MarketService) { }

    ngOnInit() {
        this._marketService.getBlocks().subscribe(blocks => this.blocks = blocks);
    }
}
