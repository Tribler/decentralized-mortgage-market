import { Component, OnInit } from '@angular/core';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'mortgages',
    template: `
         <banker-mortgages *ngIf="marketService.me?.role == 'FINANCIAL_INSTITUTION'"></banker-mortgages>
         <borrower-mortgages *ngIf="marketService.me?.role == 'BORROWER'"></borrower-mortgages>
    `
})
export class MortgagesComponent implements OnInit {
    constructor(public marketService: MarketService) { }

    ngOnInit() {
    }
}
