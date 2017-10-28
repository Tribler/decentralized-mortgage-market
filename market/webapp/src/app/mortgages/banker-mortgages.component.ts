import { Component, OnInit, OnDestroy } from '@angular/core';
import { Observable } from 'rxjs/Rx';
import { CurrencyPipe } from '@angular/common';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'banker-mortgages',
    templateUrl: './banker-mortgages.component.html'
})
export class BankerMortgagesComponent implements OnInit, OnDestroy {
    subscription;
    loan_requests = [];
    mortgages = [];
    contracts = {};

    request = {};

    constructor(public marketService: MarketService) { }

    ngOnInit() {
        this.subscription = Observable.timer(0, 5000).subscribe(t => this.loadLoanRequests());
    }

    ngOnDestroy() {
        this.subscription.unsubscribe();
    }

    loadLoanRequests() {
        this.marketService.getLoanRequests()
            .subscribe(loan_requests => this.loan_requests = loan_requests.filter((lr: any) => lr.status == 'PENDING'));
        this.marketService.getMortgages()
            .subscribe(mortgages => {
                var me: any = this.marketService.me;
                this.mortgages = mortgages.filter((m: any) => m.bank_id == me.id);
                this.marketService.getContracts(mortgages)
                    .subscribe((contracts: any) => this.contracts = contracts);
            });
    }

    acceptLoanRequest(modal) {
        var loan_request = this.request['loan_request'];
        delete this.request['loan_request'];
        this.marketService.acceptLoanRequest(loan_request, this.request)
            .subscribe(() => this.loadLoanRequests());
        modal.hide();
    }

    rejectLoanRequest(loan_request) {
        this.marketService.rejectLoanRequest(loan_request)
            .subscribe(() => this.loadLoanRequests());
    }
}
