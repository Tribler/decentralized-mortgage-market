import { Component, OnInit } from '@angular/core';

import { MarketService } from './shared/market.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
    me;

    constructor(private _marketService: MarketService) { }

    ngOnInit() {
        this._marketService.getMyUser().subscribe(me => this.me = me);
    }
}
