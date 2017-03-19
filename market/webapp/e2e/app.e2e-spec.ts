import { MarketPage } from './app.po';

describe('market App', () => {
  let page: MarketPage;

  beforeEach(() => {
    page = new MarketPage();
  });

  it('should display message saying app works', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('app works!');
  });
});
