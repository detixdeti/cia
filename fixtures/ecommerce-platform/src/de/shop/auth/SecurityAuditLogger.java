package de.shop.auth;

public class SecurityAuditLogger {
    public void logSuccessfulLogin(String customerId) {
        // log success
    }

    public void logFailedLogin(String email, String reason) {
        // log fail
    }

    public void logAccountLock(String customerId, String reason) {
        // log lock
    }
}
