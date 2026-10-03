package de.shop.customer;

public class Address {
    private String id;
    private String street;
    private String zipCode;
    private String city;
    private String country;
    private boolean isDefaultBilling;
    private boolean isDefaultShipping;

    public Address(String id, String street, String zipCode, String city, String country) {
        this.id = id;
        this.street = street;
        this.zipCode = zipCode;
        this.city = city;
        this.country = country;
    }

    public String getId() { return id; }
    public String getStreet() { return street; }
    public String getZipCode() { return zipCode; }
    public String getCity() { return city; }
    public String getCountry() { return country; }
    public boolean isDefaultShipping() { return isDefaultShipping; }
    public void setDefaultShipping(boolean val) { this.isDefaultShipping = val; }
}
