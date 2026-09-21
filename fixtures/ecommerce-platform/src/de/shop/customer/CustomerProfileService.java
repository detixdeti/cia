package de.shop.customer;

import java.util.List;
import java.util.ArrayList;

public class CustomerProfileService {
    private CustomerRepository customerRepo;

    public CustomerProfileService(CustomerRepository customerRepo) {
        this.customerRepo = customerRepo;
    }

    public Customer getProfile(String customerId) {
        return customerRepo.findById(customerId);
    }

    public boolean updateProfile(String customerId, String newName, String newEmail) {
        Customer c = customerRepo.findById(customerId);
        if (c == null) return false;
        c.setName(newName);
        c.setEmail(newEmail);
        customerRepo.save(c);
        return true;
    }

    public void addAddress(String customerId, Address address) {
        customerRepo.saveAddress(customerId, address);
    }

    public void anonymizeCustomer(String customerId) {
        Customer c = customerRepo.findById(customerId);
        if (c != null) {
            c.setName("Anonymized");
            c.setEmail("deleted-" + customerId + "@shop.local");
            c.setActive(false);
            customerRepo.save(c);
        }
    }
}
