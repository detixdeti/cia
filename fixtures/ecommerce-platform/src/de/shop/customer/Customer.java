package de.shop.customer;

import java.util.Date;

public class Customer {
    private String id;
    private String name;
    private String email;
    private boolean active;
    private Date registeredAt;

    public Customer(String id, String name, String email) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.active = true;
        this.registeredAt = new Date();
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }
    public Date getRegisteredAt() { return registeredAt; }
}
