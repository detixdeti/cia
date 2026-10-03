package de.shop.auth;

import de.shop.customer.Customer;
import de.shop.customer.CustomerRepository;

public class AuthenticationService {
    private CustomerRepository customerRepo;
    private UserSessionManager sessionManager;
    private SecurityAuditLogger auditLogger;

    public AuthenticationService(CustomerRepository repo, UserSessionManager sm, SecurityAuditLogger logger) {
        this.customerRepo = repo;
        this.sessionManager = sm;
        this.auditLogger = logger;
    }

    public String login(String email, String password) {
        Customer c = customerRepo.findByEmail(email);
        if (c == null || !c.isActive()) {
            auditLogger.logFailedLogin(email, "User not found or inactive");
            return null;
        }
        UserCredentials creds = customerRepo.getCredentials(c.getId());
        if (creds != null && creds.verifyPassword(password) && !creds.isLocked()) {
            auditLogger.logSuccessfulLogin(c.getId());
            return sessionManager.createSession(c.getId());
        }
        auditLogger.logFailedLogin(email, "Invalid password");
        return null;
    }

    public void logout(String sessionId) {
        sessionManager.invalidate(sessionId);
    }
}
