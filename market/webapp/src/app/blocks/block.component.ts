import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'block',
    templateUrl: 'block.component.html',
    styleUrls: ['./blocks.component.css']
})
export class BlockComponent implements OnInit {
    block = {};

    constructor(public marketService: MarketService,
                private _activatedRoute: ActivatedRoute) { }

    ngOnInit() {
        this._activatedRoute.params
            .map(params => params['id'])
            .subscribe(id => {
                this.marketService.getBlock(id).subscribe(block => this.block = block);
            });
    }
}
