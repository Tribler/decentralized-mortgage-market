import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/Rx';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'banker-mortgages',
    templateUrl: './banker-mortgages.component.html'
})
export class BankerMortgagesComponent implements OnInit {
    loan_requests = [];
    mortgages = [];

    request = {};

    constructor(public marketService: MarketService) { }

    ngOnInit() {
        Observable.timer(0, 5000).subscribe(t => this.loadLoanRequests());
    }

    loadLoanRequests() {
        this.marketService.getLoanRequests()
            .subscribe(loan_requests => this.loan_requests = loan_requests.filter((lr: any) => lr.status == 'PENDING'));
        this.marketService.getMortgages()
            .subscribe(mortgages => this.mortgages = mortgages);
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
