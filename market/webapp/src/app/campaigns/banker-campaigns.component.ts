import { Component, OnInit, OnDestroy } from '@angular/core';
import { Observable } from 'rxjs/Rx';
import { CurrencyPipe } from '@angular/common';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'banker-campaigns',
    templateUrl: './banker-campaigns.component.html'
})
export class BankerCampaignsComponent implements OnInit, OnDestroy {
    subscription;
    campaigns = [];
    pending_investments = [];
    accepted_investments = [];
    contracts = {};

    alert;
    selected = [];

    constructor(public marketService: MarketService) {
    }

    ngOnInit() {
        this.subscription = Observable.timer(0, 5000).subscribe(t => {
            this.loadMyCampaigns();
        });
    }

    ngOnDestroy() {
        this.subscription.unsubscribe();
    }

    loadMyCampaigns() {
        this.marketService.getMyCampaigns()
            .subscribe(campaigns => {
                this.campaigns = campaigns;

                var all_investments = [];
                campaigns.forEach((campaign: any) => {
                    campaign.investments.forEach((investment: any) => {
                        investment.mortgage_id = campaign.mortgage_id;
                    });
                    all_investments = all_investments.concat(campaign.investments);
                });

                this.pending_investments = all_investments.filter((i: any) => i.status == 'PENDING');
                this.accepted_investments = all_investments.filter((i: any) => i.status == 'ACCEPTED');

                this.marketService.getContracts(this.accepted_investments)
                    .subscribe((contracts: any) => this.contracts = contracts);
            });
    }

    acceptInvestmentOffer(investment) {
        this.marketService.acceptInvestmentOffer(investment)
             .subscribe(() => this.loadMyCampaigns());
    }

    rejectInvestmentOffer(investment) {
        this.marketService.rejectInvestmentOffer(investment)
            .subscribe(() => this.loadMyCampaigns());
    }
}
