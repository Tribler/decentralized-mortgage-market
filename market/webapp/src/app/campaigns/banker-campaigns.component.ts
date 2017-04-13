import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/Rx';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'banker-campaigns',
    templateUrl: './banker-campaigns.component.html'
})
export class BankerCampaignsComponent implements OnInit {
    campaigns = [];
    pending_investments = [];
    accepted_investments = [];

    alert;
    selected = [];

    constructor(public marketService: MarketService) {
    }

    ngOnInit() {
        Observable.timer(0, 5000).subscribe(t => {
            this.loadMyCampaigns();
        });
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
        this.marketService.acceptInvestment(investment)
             .subscribe(() => this.loadMyCampaigns());
    }

    rejectInvestmentOffer(investment) {
        this.marketService.rejectInvestment(investment)
            .subscribe(() => this.loadMyCampaigns());
    }
}
