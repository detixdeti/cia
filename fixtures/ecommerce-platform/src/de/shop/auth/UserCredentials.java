package de.shop.auth;

public class UserCredentials {
    private String customerId;
    private String passwordHash;
    private String salt;
    private boolean locked;

    public UserCredentials(String customerId, String passwordHash, String salt) {
        this.customerId = customerId;
        this.passwordHash = passwordHash;
        this.salt = salt;
        this.locked = false;
    }

    public String getCustomerId() { return customerId; }
    public boolean verifyPassword(String candidate) {
        return passwordHash != null && passwordHash.equals(candidate);
    }
    public void updatePassword(String newHash, String newSalt) {
        this.passwordHash = newHash;
        this.salt = newSalt;
    }
    public boolean isLocked() { return locked; }
    public void setLocked(boolean locked) { this.locked = locked; }
}
