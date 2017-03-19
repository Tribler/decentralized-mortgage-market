import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { InvestorCampaignsComponent } from './investor-mortgages.component';

describe('InvestorCampaignsComponent', () => {
  let component: InvestorCampaignsComponent;
  let fixture: ComponentFixture<InvestorCampaignsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ InvestorCampaignsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(InvestorCampaignsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
