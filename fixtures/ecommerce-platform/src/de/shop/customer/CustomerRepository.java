package de.shop.customer;

import java.util.HashMap;
import java.util.Map;
import de.shop.auth.UserCredentials;

public class CustomerRepository {
    private Map<String, Customer> customers = new HashMap<>();
    private Map<String, UserCredentials> credentials = new HashMap<>();

    public Customer findById(String id) { return customers.get(id); }
    public Customer findByEmail(String email) {
        for (Customer c : customers.values()) {
            if (c.getEmail().equalsIgnoreCase(email)) return c;
        }
        return null;
    }
    public void save(Customer customer) { customers.put(customer.getId(), customer); }
    public UserCredentials getCredentials(String customerId) { return credentials.get(customerId); }
    public void saveCredentials(UserCredentials creds) { credentials.put(creds.getCustomerId(), creds); }
    public void saveAddress(String customerId, Address address) { }
}
