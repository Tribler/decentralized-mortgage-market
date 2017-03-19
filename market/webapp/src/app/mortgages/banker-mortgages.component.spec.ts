import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BankerMortgagesComponent } from './banker-mortgages.component';

describe('BankerMortgagesComponent', () => {
  let component: BankerMortgagesComponent;
  let fixture: ComponentFixture<BankerMortgagesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BankerMortgagesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BankerMortgagesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
