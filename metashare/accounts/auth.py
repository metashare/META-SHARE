"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging
from Crypto.PublicKey import RSA
from base64 import b64decode
from datetime import datetime
from django.contrib.auth.models import User
from metashare.accounts.models import UserProfile
from metashare.accounts.views import _check_sso_token
from metashare.settings import LOG_LEVEL, LOG_HANDLER, PRIVATE_KEY_PATH, \
  MAX_LIFETIME_FOR_SSO_TOKENS

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.accounts.auth')
LOGGER.addHandler(LOG_HANDLER)

class SingleSignOnTokenBackend(object):
    """
    Authenticate against a token to allow login via SSO redirect.
    """
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, uuid=None, timestamp=None, token=None):
        """
        Authenticates the user matching the given uuid.
        """
        # Try to authenticate using the SSO secret key for managing nodes.
        if len(token) == 32:
            if _check_sso_token(uuid, timestamp, token):
                LOGGER.info('Received valid SSO token for uuid {0}.'.format(
                  uuid))
                profile = UserProfile.objects.filter(uuid=uuid)
                if profile:
                    LOGGER.info('Found valid user account {0}.'.format(
                      profile[0].user.username))
                    return profile[0].user
        
        # If that did not work, we try to authenticate for non-managing nodes.
        else:
            # Load private key from PRIVATE_KEY_PATH file.
            with open(PRIVATE_KEY_PATH, 'r') as pem:
                my_private_pem = pem.read()
            
            # Create private key for local django instance.
            my_private_key = RSA.importKey(my_private_pem)
            
            # Decrypt given token and check uuid and timestamp.
            _token = my_private_key.decrypt(b64decode(token))
            _uuid = _token[:32]
            _timestamp = _token[32:]
            
            # Compute timedelta between now and the given timestamp.
            _delta =  datetime.now() - datetime.fromtimestamp(int(_timestamp))

            # Timestamp outdated? Compare to MAX_LIFETIME_FOR_SSO_TOKENS.
            if abs(_delta.total_seconds()) >= MAX_LIFETIME_FOR_SSO_TOKENS:
                LOGGER.info('Outdated SSO token used!')
                return None
            
            if _uuid == uuid and _timestamp == timestamp:
                LOGGER.info('Found valid MetaShareUser account.')
                metashareuser = User.objects.filter(username='MetaShareUser')
                if metashareuser:
                    return metashareuser[0]
        
        return None

    def get_user(self, user_id):
        """
        Retursn the user instance for the given user_id.
        """
        try:
            user = User.objects.get(id=user_id)
            return user
        
        except User.DoesNotExist:
            return None
        
        return None
