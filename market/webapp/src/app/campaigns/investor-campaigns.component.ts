import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/Rx';

import { MarketService } from '../shared/market.service';

@Component({
    selector: 'investor-campaigns',
    templateUrl: './investor-campaigns.component.html'
})
export class InvestorCampaignsComponent implements OnInit {
    investments = [];
    campaigns = [];

    alert;
    request = {};

    constructor(private _marketService: MarketService) { }

    ngOnInit() {
        Observable.timer(0, 5000).subscribe(t => {
            this.loadMyInvestments();
            this.loadCampaigns();
        });
    }

    loadMyInvestments() {
        this._marketService.getMyInvestments()
            .subscribe(investments => this.investments = investments);
    }

    loadCampaigns() {
        this._marketService.getCampaigns()
            .map(campaigns => campaigns.filter((campaign: any) => !campaign.completed))
            .subscribe(campaigns => this.campaigns = campaigns);
    }

    offerInvestment(modal) {
        this._marketService.addMyInvestment(this.request)
            .subscribe(() => {
                           this.loadMyInvestments();
                           this.loadCampaigns();
                       },
                       err => this.alert = {type: 'danger', msg: 'Error from backend: ' + err.json().error});
        modal.hide();
    }
}
