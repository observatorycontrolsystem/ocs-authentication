class OCSAuthenticationException(Exception):
    pass

class OAuthTokenException(OCSAuthenticationException):
    pass

class ProfileException(OCSAuthenticationException):
    pass
