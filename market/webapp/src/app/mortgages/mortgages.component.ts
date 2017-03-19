import { Component, OnInit } from '@angular/core';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'mortgages',
    template: `
         <banker-mortgages *ngIf="me?.role == 'FINANCIAL_INSTITUTION'"></banker-mortgages>
         <borrower-mortgages *ngIf="me?.role == 'BORROWER'"></borrower-mortgages>
    `
})
export class MortgagesComponent implements OnInit {
    me;

    constructor(private _marketService: MarketService) { }

    ngOnInit() {
        this._marketService.getMyUser().subscribe(me => this.me = me);
    }
}
