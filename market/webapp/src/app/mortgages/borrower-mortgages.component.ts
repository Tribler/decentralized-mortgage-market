import { Component, OnInit, OnDestroy } from '@angular/core';
import { Observable } from 'rxjs/Rx';
import { CurrencyPipe } from '@angular/common';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'borrower-mortgages',
    templateUrl: './borrower-mortgages.component.html'
})
export class BorrowerMortgagesComponent implements OnInit, OnDestroy {
    subscription;
    loan_requests = [];
    mortgages = [];
    contracts = {};

    alert;
    request = {};

    constructor(public marketService: MarketService) {
    }

    ngOnInit() {
        this.subscription = Observable.timer(0, 5000).subscribe(t => {
            this.loadMyMortgages();
            this.loadMyLoanRequests();
        });
    }

    ngOnDestroy() {
        this.subscription.unsubscribe();
    }

    loadMyLoanRequests() {
        this.marketService.getMyLoanRequests()
            .subscribe(loan_requests => this.loan_requests = loan_requests.filter((lr: any) => lr.status != 'ACCEPTED'));
    }

    loadMyMortgages() {
        this.marketService.getMyMortgages()
            .subscribe(mortgages => {
                this.mortgages = mortgages;
                this.marketService.getContracts(mortgages)
                    .subscribe((contracts: any) => this.contracts = contracts);
            });
    }

    requestLoan(modal) {
        this.marketService.addMyLoanRequest(this.request)
            .subscribe(() => this.loadMyLoanRequests(),
                       err => this.alert = {type: 'danger', msg: 'Error from backend: ' + err.json().error});
        modal.hide();
    }

    acceptMortgageOffer(mortgage) {
        this.marketService.acceptMyMortgageOffer(mortgage)
            .subscribe();
    }

    rejectMortgageOffer(mortgage) {
        this.marketService.rejectMyMortgageOffer(mortgage)
            .subscribe();
    }
}
