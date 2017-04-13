import { Component, OnInit } from '@angular/core';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'campaigns',
    template: `
         <investor-campaigns *ngIf="marketService.me?.role == 'INVESTOR'"></investor-campaigns>
         <banker-campaigns *ngIf="marketService.me?.role == 'FINANCIAL_INSTITUTION'"></banker-campaigns>
    `
})
export class CampaignsComponent implements OnInit {

    constructor(public marketService: MarketService) { }

    ngOnInit() {
    }
}
