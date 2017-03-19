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
    acceptMyMortgageOffer(id): Observable<String> {
        return this._http.patch(this._api_base + `/you/mortgages/${id}`, JSON.stringify({status: 'ACCEPT'}))
            .map(res => res.json());
    }
    rejectMyMortgageOffer(id): Observable<String> {
        return this._http.patch(this._api_base + `/you/mortgages/${id}`, JSON.stringify({status: 'REJECT'}))
            .map(res => res.json());
    }

    getLoanRequests(): Observable<Object[]> {
        return this._http.get(this._api_base + '/loanrequests')
            .map(res => res.json().loan_requests);
    }
    acceptLoanRequest(id): Observable<String> {
        return this._http.patch(this._api_base + `/loanrequests/${id}`, JSON.stringify({status: 'ACCEPT'}))
            .map(res => res.json());
    }
    rejectLoanRequest(id): Observable<String> {
        return this._http.patch(this._api_base + `/loanrequests/${id}`, JSON.stringify({status: 'REJECT'}))
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
    acceptInvestment(campaign_id, investment_id): Observable<String> {
        return this._http.patch(this._api_base + `/campaigns/${campaign_id}/investments/${investment_id}`,
                                JSON.stringify({status: 'ACCEPT'}))
            .map(res => res.json());
    }
    rejectInvestment(campaign_id, investment_id): Observable<String> {
        return this._http.patch(this._api_base + `/campaigns/${campaign_id}/investments/${investment_id}`,
                                JSON.stringify({status: 'REJECT'}))
            .map(res => res.json());
    }
}
