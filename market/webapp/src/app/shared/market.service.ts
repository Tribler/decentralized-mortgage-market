import { Http } from '@angular/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';


@Injectable()
export class MarketService {
    private _api_base = '/api';

    constructor(private _http: Http) {
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

    getMyMortgages(): Observable<Object[]> {
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

    getMortgages(): Observable<Object[]> {
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

    getMyInvestments(): Observable<Object[]> {
        return this._http.get(this._api_base + '/you/investments')
            .map(res => res.json().investments);
    }
    addMyInvestment(investment): Observable<Object[]> {
        return this._http.put(this._api_base + '/you/investments', investment)
            .map(res => res.json().success);
    }
    acceptInvestment(investment): Observable<String> {
        return this._http.patch(this._api_base + `/campaigns/${investment.campaign_id} ${investment.campaign_user_id}/investments/${investment.id} ${investment.user_id}`,
                                JSON.stringify({status: 'ACCEPT'}))
            .map(res => res.json());
    }
    rejectInvestment(investment): Observable<String> {
        return this._http.patch(this._api_base + `/campaigns/${investment.campaign_id} ${investment.campaign_user_id}/investments/${investment.id} ${investment.user_id}`,
                                JSON.stringify({status: 'REJECT'}))
            .map(res => res.json());
    }
}
