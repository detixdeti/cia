package de.shop.auth;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public class UserSessionManager {
    private Map<String, String> sessions = new HashMap<>();

    public String createSession(String customerId) {
        String sessionId = UUID.randomUUID().toString();
        sessions.put(sessionId, customerId);
        return sessionId;
    }

    public String getCustomerId(String sessionId) {
        return sessions.get(sessionId);
    }

    public void invalidate(String sessionId) {
        sessions.remove(sessionId);
    }
}
