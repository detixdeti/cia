package de.shop.customer;

public class PaymentMethod {
    private String id;
    private String customerId;
    private String type;
    private String token;
    private boolean preferred;

    public PaymentMethod(String id, String customerId, String type, String token) {
        this.id = id;
        this.customerId = customerId;
        this.type = type;
        this.token = token;
        this.preferred = false;
    }

    public String getId() { return id; }
    public String getCustomerId() { return customerId; }
    public String getType() { return type; }
    public String getToken() { return token; }
    public boolean isPreferred() { return preferred; }
    public void setPreferred(boolean preferred) { this.preferred = preferred; }
}
