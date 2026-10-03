package de.shop.shipping;

import de.shop.inventory.StockService;

public class ReturnProcessingService {
    private StockService stockService;

    public ReturnProcessingService(StockService stockService) {
        this.stockService = stockService;
    }

    public void processReturn(ReturnPackage ret) {
        ret.setInspectResult("PASSED");
        for (String sku : ret.getReturnedSkus()) {
            stockService.addInventory(sku, 1, 5);
        }
    }
}
