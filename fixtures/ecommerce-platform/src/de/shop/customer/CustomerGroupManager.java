package de.shop.customer;

import java.util.HashMap;
import java.util.Map;

public class CustomerGroupManager {
    private Map<String, String> customerGroups = new HashMap<>();

    public void assignGroup(String customerId, String groupName) {
        customerGroups.put(customerId, groupName);
    }

    public String getGroup(String customerId) {
        return customerGroups.getOrDefault(customerId, "STANDARD");
    }

    public double getGroupDiscount(String groupName) {
        if ("VIP".equals(groupName)) return 0.10;
        if ("WHOLESALE".equals(groupName)) return 0.20;
        return 0.0;
    }
}
