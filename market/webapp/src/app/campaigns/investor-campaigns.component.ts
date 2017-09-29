import { Component, OnInit, OnDestroy } from '@angular/core';
import { Observable } from 'rxjs/Rx';
import { CurrencyPipe } from '@angular/common';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'investor-campaigns',
    templateUrl: './investor-campaigns.component.html'
})
export class InvestorCampaignsComponent implements OnInit, OnDestroy {
    subscription;
    my_investments = [];
    investments = [];
    campaigns = [];

    alert;
    investment_offer = {};
    transfer_offer = {};

    constructor(public marketService: MarketService) { }

    ngOnInit() {
        this.subscription = Observable.timer(0, 5000).subscribe(t => {
            this.update();
        });
    }

    ngOnDestroy() {
        this.subscription.unsubscribe();
    }

    update() {
        this.loadCampaigns();
        this.loadInvestments();
    }

    loadCampaigns() {
        this.marketService.getCampaigns()
            .map(campaigns => campaigns.filter((campaign: any) => campaign.amount_invested < campaign.amount))
            .subscribe(campaigns => this.campaigns = campaigns);
    }

    loadInvestments() {
        this.marketService.getMyInvestments()
            .subscribe(my_investments => {
                this.my_investments = my_investments
                this.marketService.getInvestments()
                    .map(investments => investments.filter((investment: any) => investment.status == 'FORSALE'))
                    .map(investments => investments.filter((investment: any) => {
                        // Filter out my investments
                        var mine = false;
                        this.my_investments.forEach(function(v, i) {
                            if (v.id == investment.id && v.user_id == investment.user_id)
                               mine = true;
                        });
                        return !mine;         
                    }))
                    .subscribe(investments => this.investments = investments);
            });
    }

    offerInvestment(modal) {
        this.marketService.addMyInvestment(this.investment_offer)
            .subscribe(() => this.update(), err => this.setErrorMessage(err.json().error));
        modal.hide();
    }

    sellMyInvestment(investment) {
        this.marketService.sellMyInvestment(investment)
            .subscribe(() => this.update(), err => this.setErrorMessage(err.json().error));
    }

    offerTransfer(modal) {
        this.marketService.offerTransfer(this.transfer_offer)
            .subscribe(() => this.update(), err => this.setErrorMessage(err.json().error));
        modal.hide();
    }

    acceptTransferOffer(investment) {
        this.marketService.acceptTransfer(investment.best_offer)
            .subscribe(() => this.update(), err => this.setErrorMessage(err.json().error));
    }

    setErrorMessage(message) {
        this.alert = {type: 'danger', msg: 'Error from backend: ' + message}
    }

    canMakeTransferOffer(investment) {
        var offer_made = false;
        investment.transfers.forEach(function(transfer, index) {
            if (transfer.status == 'PENDING') {
                offer_made = true;
            }
        });
        return investment.status == 'FORSALE' && !offer_made;
    }
}
