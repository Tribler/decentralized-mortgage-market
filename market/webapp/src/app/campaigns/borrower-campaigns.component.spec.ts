import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BorrowerCampaignsComponent } from './borrower-campaigns.component';

describe('BorrowerCampaignsComponent', () => {
  let component: BorrowerCampaignsComponent;
  let fixture: ComponentFixture<BorrowerCampaignsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BorrowerCampaignsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BorrowerCampaignsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
