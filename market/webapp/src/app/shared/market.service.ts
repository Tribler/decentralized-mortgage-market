import { Http } from '@angular/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';

import { Mortgage } from './mortgage.model';
import { Investment } from './investment.model';
import { Block } from './block.model';
import { Contract } from './contract.model';

@Injectable()
export class MarketService {
    private _api_base = '/api';

    me = {};
    users = {};
    online_banks = [];
    constructor(private _http: Http) {
        Observable.timer(0, 60000).subscribe(t => {
            this.getMyUser().subscribe(me => Object.assign(this.me, me));

            var self = this;
            this.getUsers().subscribe(users => {
                this.online_banks = users.filter((user: any) => user.role === 'FINANCIAL_INSTITUTION' && user.online);

                // Reset self.users
                for (var user_id in self.users) {
                    delete self.users[user_id];
                }
                users.forEach(function(item: any, index, array) {
                    self.users[item.id] = item;
                });
            });
        });
    }

    getDisplayname(user_id): string {
        return (this.users[user_id] || {}).display_name || user_id.slice(-10);
    }

    getMyUser(): Observable<Object[]> {
        return this._http.get(this._api_base + '/you')
            .map(res => res.json().you);
    }
    getMyProfile(): Observable<Object[]> {
        return this._http.get(this._api_base + '/you/profile')
            .map(res => res.json().profile);
    }
    saveMyProfile(profile): Observable<Object[]> {
        return this._http.put(this._api_base + '/you/profile', profile)
            .map(res => res.json().success);
    }

    getUsers(): Observable<Object[]> {
        return this._http.get(this._api_base + '/users')
            .map(res => res.json().users);
    }

    getMyLoanRequests(): Observable<Object[]> {
        return this._http.get(this._api_base + '/you/loanrequests')
            .map(res => res.json().loan_requests);
    }
    addMyLoanRequest(loan_request): Observable<Object[]> {
        return this._http.put(this._api_base + '/you/loanrequests', loan_request)
            .map(res => res.json().success);
    }

    getMyMortgages(): Observable<Mortgage[]> {
        return this._http.get(this._api_base + '/you/mortgages')
            .map(res => res.json().mortgages);
    }
    acceptMyMortgageOffer(mortgage): Observable<String> {
        return this._http.patch(this._api_base + `/you/mortgages/${mortgage.id} ${mortgage.user_id}`, JSON.stringify({status: 'ACCEPT'}))
            .map(res => res.json());
    }
    rejectMyMortgageOffer(mortgage): Observable<String> {
        return this._http.patch(this._api_base + `/you/mortgages/${mortgage.id} ${mortgage.user_id}`, JSON.stringify({status: 'REJECT'}))
            .map(res => res.json());
    }

    getMortgages(): Observable<Mortgage[]> {
        return this._http.get(this._api_base + '/mortgages')
            .map(res => res.json().mortgages);
    }
    getLoanRequests(): Observable<Object[]> {
        return this._http.get(this._api_base + '/loanrequests')
            .map(res => res.json().loan_requests);
    }
    acceptLoanRequest(loan_request, params): Observable<String> {
        params.status = 'ACCEPT';
        return this._http.patch(this._api_base + `/loanrequests/${loan_request.id} ${loan_request.user_id}`, JSON.stringify(params))
            .map(res => res.json());
    }
    rejectLoanRequest(loan_request): Observable<String> {
        return this._http.patch(this._api_base + `/loanrequests/${loan_request.id} ${loan_request.user_id}`, JSON.stringify({status: 'REJECT'}))
            .map(res => res.json());
    }

    getMyCampaigns(): Observable<Object[]> {
        return this._http.get(this._api_base + '/you/campaigns')
            .map(res => res.json().campaigns);
    }
    getCampaigns(): Observable<Object[]> {
        return this._http.get(this._api_base + '/campaigns')
            .map(res => res.json().campaigns);
    }

    getMyInvestments(): Observable<Investment[]> {
        return this._http.get(this._api_base + '/you/investments')
            .map(res => res.json().investments);
    }
    addMyInvestment(investment): Observable<String> {
        return this._http.put(this._api_base + '/you/investments', investment)
            .map(res => res.json().success);
    }
    sellMyInvestment(investment): Observable<String> {
        return this._http.patch(this._api_base + `/you/investments/${investment.id} ${investment.user_id}`,
                                JSON.stringify({status: 'FORSALE'}))
            .map(res => res.json());
    }

    offerTransfer(transfer): Observable<String> {
        return this._http.put(this._api_base + `/investments/${transfer.investment_id} ${transfer.investment_user_id}/transfers`, transfer)
            .map(res => res.json());
    }
    acceptTransfer(transfer): Observable<String> {
        return this._http.patch(this._api_base + `/investments/${transfer.investment_id} ${transfer.investment_user_id}/transfers/${transfer.id} ${transfer.user_id}`, JSON.stringify({status: 'ACCEPT'}))
            .map(res => res.json());
    }
    declineTransfer(transfer): Observable<String> {
        return this._http.patch(this._api_base + `/investments/${transfer.investment_id} ${transfer.investment_user_id}/transfers/${transfer.id} ${transfer.user_id}`, JSON.stringify({status: 'DECLINE'}))
            .map(res => res.json());
    }


    getInvestments(): Observable<Investment[]> {
        return this._http.get(this._api_base + '/investments')
            .map(res => res.json().investments);
    }
    acceptInvestmentOffer(investment): Observable<String> {
        return this._http.patch(this._api_base + `/campaigns/${investment.campaign_id} ${investment.campaign_user_id}/investments/${investment.id} ${investment.user_id}`,
                                JSON.stringify({status: 'ACCEPT'}))
            .map(res => res.json());
    }
    rejectInvestmentOffer(investment): Observable<String> {
        return this._http.patch(this._api_base + `/campaigns/${investment.campaign_id} ${investment.campaign_user_id}/investments/${investment.id} ${investment.user_id}`,
                                JSON.stringify({status: 'REJECT'}))
            .map(res => res.json());
    }

    getBlock(block_id): Observable<Block[]> {
        return this._http.get(this._api_base + `/blocks/${block_id}`)
            .map(res => res.json().block);
    }
    getBlocks(): Observable<Block[]> {
        return this._http.get(this._api_base + '/blocks')
            .map(res => res.json().blocks);
    }

    getContract(contract_id): Observable<Contract[]> {
        return this._http.get(this._api_base + `/contracts/${contract_id}`)
            .map(res => res.json().contract);
    }
    getContracts(items): Observable<Contract[]> {
        var contract_ids = [];
        items.forEach((item: any) => contract_ids.push(this.getOwnershipContract(item)));
        return this._http.post(this._api_base + '/contracts', contract_ids)
            .map(res => res.json().contracts);
    }

    getOwnershipContract(item): string {
        return (item.transfers && item.transfers.length) ?
               item.transfers[item.transfers.length-1].confirmation_contract_id : item.contract_id;
    }
}
