import { Component, OnInit } from '@angular/core';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'blocks',
    templateUrl: 'blocks.component.html',
    styleUrls: ['./blocks.component.css']
})
export class BlocksComponent implements OnInit {
    blocks = [];

    constructor(public marketService: MarketService) { }

    ngOnInit() {
        this.marketService.getBlocks().subscribe(blocks => this.blocks = blocks);
    }
}
