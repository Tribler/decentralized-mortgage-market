import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/Rx';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'borrower-mortgages',
    templateUrl: './borrower-mortgages.component.html'
})
export class BorrowerMortgagesComponent implements OnInit {
    loan_requests = [];
    mortgages = [];
    banks = [];

    alert;
    request = {};

    constructor(private _marketService: MarketService) {
    }

    ngOnInit() {
        this.loadBanks();

        Observable.timer(0, 5000).subscribe(t => {
            this.loadMyMortgages();
            this.loadMyLoanRequests();
        });
    }

    loadBanks() {
        this._marketService.getUsers()
            .subscribe(users => this.banks = users.filter((user: any) => user.role === 'FINANCIAL_INSTITUTION'));
    }

    loadMyLoanRequests() {
        this._marketService.getMyLoanRequests()
            .subscribe(loan_requests => this.loan_requests = loan_requests.filter((lr: any) => lr.status != 'ACCEPTED'));
    }

    loadMyMortgages() {
        this._marketService.getMyMortgages()
            .subscribe(mortgages => this.mortgages = mortgages);
    }

    requestLoan(modal) {
        this._marketService.addMyLoanRequest(this.request)
            .subscribe(() => this.loadMyLoanRequests(),
                       err => this.alert = {type: 'danger', msg: 'Error from backend: ' + err.json().error});
        modal.hide();
    }

    acceptMortgageOffer(mortgage) {
        console.log(mortgage);
        this._marketService.acceptMyMortgageOffer(mortgage)
            .subscribe();
    }

    rejectMortgageOffer(mortgage) {
        this._marketService.rejectMyMortgageOffer(mortgage)
            .subscribe();
    }
}
