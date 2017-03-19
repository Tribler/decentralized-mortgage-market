import { Component, OnInit } from '@angular/core';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'campaigns',
    template: `
         <investor-campaigns *ngIf="me?.role == 'INVESTOR'"></investor-campaigns>
         <borrower-campaigns *ngIf="me?.role == 'BORROWER'"></borrower-campaigns>
    `
})
export class CampaignsComponent implements OnInit {
    me;

    constructor(private _marketService: MarketService) { }

    ngOnInit() {
        this._marketService.getMyUser().subscribe(me => this.me = me);
    }
}
