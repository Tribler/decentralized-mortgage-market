import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MortgagesComponent } from './mortgages.component';

describe('MortgagesComponent', () => {
  let component: MortgagesComponent;
  let fixture: ComponentFixture<MortgagesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MortgagesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MortgagesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
