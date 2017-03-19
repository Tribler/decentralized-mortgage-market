import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/Rx';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'borrower-mortgages',
    templateUrl: './borrower-mortgages.component.html'
})
export class BorrowerMortgagesComponent implements OnInit {
    pending_loan_requests = [];
    pending_mortgages = [];
    accepted_mortgages = [];
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
            .map(users => users.filter((user: any) => user.role === 'FINANCIAL_INSTITUTION'))
            .subscribe(banks => this.banks = banks);
    }

    loadMyLoanRequests() {
        this._marketService.getMyLoanRequests()
            .map(loan_requests => loan_requests.filter((lr: any) => lr.status == 'PENDING'))
            .subscribe(pending_loan_requests => this.pending_loan_requests = pending_loan_requests);
    }

    loadMyMortgages() {
        this._marketService.getMyMortgages()
            .subscribe(mortgages => {
                this.pending_mortgages = mortgages.filter((m: any) => m.status == 'PENDING');
                this.accepted_mortgages = mortgages.filter((m: any) => m.status == 'ACCEPTED');
            });
    }

    requestLoan(modal) {
        this._marketService.addMyLoanRequest(this.request)
            .subscribe(() => this.loadMyLoanRequests(),
                       err => this.alert = {type: 'danger', msg: 'Error from backend: ' + err.json().error});
        modal.hide();
    }

    acceptMortgageOffer(id) {
        this._marketService.acceptMyMortgageOffer(id)
            .subscribe();
    }

    rejectMortgageOffer(id) {
        this._marketService.rejectMyMortgageOffer(id)
            .subscribe();
    }
}
