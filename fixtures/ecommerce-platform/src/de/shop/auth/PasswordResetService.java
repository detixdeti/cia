package de.shop.auth;

import java.util.UUID;
import java.util.Map;
import java.util.HashMap;

public class PasswordResetService {
    private Map<String, String> tokenToCustomer = new HashMap<>();

    public String generateResetToken(String customerId) {
        String token = UUID.randomUUID().toString();
        tokenToCustomer.put(token, customerId);
        return token;
    }

    public boolean validateToken(String token) {
        return tokenToCustomer.containsKey(token);
    }

    public String consumeToken(String token) {
        return tokenToCustomer.remove(token);
    }
}
