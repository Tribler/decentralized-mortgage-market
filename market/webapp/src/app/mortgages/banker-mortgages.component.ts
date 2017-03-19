import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/Rx';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'banker-mortgages',
    templateUrl: './banker-mortgages.component.html'
})
export class BankerMortgagesComponent implements OnInit {
    pending_loan_requests = [];
    accepted_loan_requests = [];

    constructor(private _marketService: MarketService) { }

    ngOnInit() {
        Observable.timer(0, 5000).subscribe(t => this.loadLoanRequests());
    }

    loadLoanRequests() {
        this._marketService.getLoanRequests()
            .subscribe(loan_requests => {
                this.pending_loan_requests = loan_requests.filter((lr: any) => lr.status == 'PENDING');
                this.accepted_loan_requests = loan_requests.filter((lr: any) => lr.status == 'ACCEPTED');
            });
    }

    acceptLoanRequest(id) {
        this._marketService.acceptLoanRequest(id)
            .subscribe(() => this.loadLoanRequests());
    }

    rejectLoanRequest(id) {
        this._marketService.rejectLoanRequest(id)
            .subscribe(() => this.loadLoanRequests());
    }
}
