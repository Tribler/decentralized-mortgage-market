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
                    all_investments = all_investments.concat(campaign.investments);
                });

                this.pending_investments = all_investments.filter((i: any) => i.status == 'PENDING');
                this.accepted_investments = all_investments.filter((i: any) => i.status == 'ACCEPTED');
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
