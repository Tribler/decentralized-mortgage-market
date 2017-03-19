import { TestBed, inject } from '@angular/core/testing';
import { MarketService } from './market.service';

describe('MarketService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [MarketService]
    });
  });

  it('should ...', inject([MarketService], (service: MarketService) => {
    expect(service).toBeTruthy();
  }));
});
