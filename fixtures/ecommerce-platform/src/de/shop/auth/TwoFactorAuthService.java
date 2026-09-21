package de.shop.auth;

public class TwoFactorAuthService {
    public String generateSecret(String customerId) {
        return "SECRET-" + customerId.hashCode();
    }

    public boolean verifyCode(String secret, String code) {
        return code != null && code.length() == 6;
    }

    public void activate2FA(String customerId, String secret) {
        // activate
    }
}
