import { Component, OnInit, OnDestroy } from '@angular/core';
import { trigger, style, animate, transition, keyframes } from '@angular/core';
import { Observable } from 'rxjs/Rx';
import { Block } from '../shared/block.model';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'blocks',
    templateUrl: 'blocks.component.html',
    styleUrls: ['./blocks.component.css'],
    animations: [
        trigger('fade', [
            transition('void => in', [
                style({ opacity: 0 }),
                animate(1000, style({ opacity: 1 }))
            ])
        ])
    ]
})
export class BlocksComponent implements OnInit, OnDestroy {
    blocks = [];
    subscription;
    counter = 0;

    constructor(public marketService: MarketService) { }

    ngOnInit() {
        this.subscription = Observable.timer(0, 5000).subscribe(t => {
            this.marketService.getBlocks().subscribe(blocks => {
                this.blocks = blocks;
                this.counter += 1;
            });
        });
    }

    ngOnDestroy() {
        this.subscription.unsubscribe();
    }

    trackByBlocks(index: number, block: Block): string { return block.id; }
}
