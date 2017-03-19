import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/Rx';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'borrower-campaigns',
    templateUrl: './borrower-campaigns.component.html'
})
export class BorrowerCampaignsComponent implements OnInit {
    campaigns = [];
    pending_investments = [];
    accepted_investments = [];

    alert;
    selected = [];

    constructor(private _marketService: MarketService) {
    }

    ngOnInit() {
        Observable.timer(0, 5000).subscribe(t => {
            this.loadMyCampaigns();
        });
    }

    loadMyCampaigns() {
        this._marketService.getMyCampaigns()
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
        console.log(investment);
        this._marketService.acceptInvestment(investment.campaign_id, investment.id)
             .subscribe(() => this.loadMyCampaigns());
    }

    rejectInvestmentOffer(investment) {
        this._marketService.rejectInvestment(investment.campaign_id, investment.id)
            .subscribe(() => this.loadMyCampaigns());
    }
}
