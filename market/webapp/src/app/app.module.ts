import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { RouterModule, Routes } from '@angular/router';
import { HashLocationStrategy, Location, LocationStrategy } from '@angular/common';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ModalModule } from 'ng2-bootstrap/modal';
import { AlertModule } from 'ng2-bootstrap/alert';

import { AppComponent } from './app.component';
import { MarketService } from './shared/market.service';
import { StatusComponentComponent } from './shared/status-component.component';

import { ProfileComponent } from './profile/profile.component';

import { MortgagesComponent } from './mortgages/mortgages.component';
import { BankerMortgagesComponent } from './mortgages/banker-mortgages.component';
import { BorrowerMortgagesComponent } from './mortgages/borrower-mortgages.component';

import { CampaignsComponent } from './campaigns/campaigns.component';
import { BorrowerCampaignsComponent } from './campaigns/borrower-campaigns.component';
import { InvestorCampaignsComponent } from './campaigns/investor-campaigns.component';


const routes: Routes = [
    { path: '', redirectTo: 'profile', pathMatch: 'full' },
    { path: 'profile', component: ProfileComponent },
    { path: 'mortgages', component: MortgagesComponent },
    { path: 'campaigns', component: CampaignsComponent }
];

@NgModule({
    declarations: [
        AppComponent,
        ProfileComponent,
        MortgagesComponent,
        BankerMortgagesComponent,
        BorrowerMortgagesComponent,
        CampaignsComponent,
        BorrowerCampaignsComponent,
        InvestorCampaignsComponent,
        StatusComponentComponent,
    ],
    imports: [
        BrowserModule,
        FormsModule,
        HttpModule,
        RouterModule.forRoot(routes),
        NgxDatatableModule,
        ModalModule.forRoot(),
        AlertModule.forRoot(),
    ],
    providers: [Location,
        { provide: LocationStrategy, useClass: HashLocationStrategy },
        MarketService,
    ],
    bootstrap: [AppComponent]
})
export class AppModule { }
