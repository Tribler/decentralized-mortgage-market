import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BorrowerMortgagesComponent } from './borrower-mortgages.component';

describe('BorrowerMortgagesComponent', () => {
  let component: BorrowerMortgagesComponent;
  let fixture: ComponentFixture<BorrowerMortgagesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BorrowerMortgagesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BorrowerMortgagesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
