package de.shop.shipping;

import java.util.List;
import java.util.ArrayList;

public class ReturnPackage {
    private String returnId;
    private String orderId;
    private List<String> returnedSkus = new ArrayList<>();
    private String inspectResult;

    public ReturnPackage(String returnId, String orderId) {
        this.returnId = returnId;
        this.orderId = orderId;
    }

    public String getReturnId() { return returnId; }
    public String getOrderId() { return orderId; }
    public List<String> getReturnedSkus() { return returnedSkus; }
    public void addSku(String sku) { returnedSkus.add(sku); }
    public String getInspectResult() { return inspectResult; }
    public void setInspectResult(String res) { this.inspectResult = res; }
}
