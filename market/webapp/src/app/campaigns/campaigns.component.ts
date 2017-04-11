import { Component, OnInit } from '@angular/core';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'campaigns',
    template: `
         <investor-campaigns *ngIf="me?.role == 'INVESTOR'"></investor-campaigns>
         <banker-campaigns *ngIf="me?.role == 'FINANCIAL_INSTITUTION'"></banker-campaigns>
    `
})
export class CampaignsComponent implements OnInit {
    me;

    constructor(private _marketService: MarketService) { }

    ngOnInit() {
        this._marketService.getMyUser().subscribe(me => this.me = me);
    }
}
