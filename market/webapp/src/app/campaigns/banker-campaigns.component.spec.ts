import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BankerCampaignsComponent } from './banker-campaigns.component';

describe('BankerCampaignsComponent', () => {
  let component: BankerCampaignsComponent;
  let fixture: ComponentFixture<BankerCampaignsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BankerCampaignsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BankerCampaignsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
