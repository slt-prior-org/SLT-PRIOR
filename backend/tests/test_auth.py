import pytest
import sys
import os

# Must be set before importing config, otherwise raises RuntimeError
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALG", "HS256")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jose import jwt, JWTError
from routes.auth import create_access_token, pwd_context
from config import settings

pytestmark = pytest.mark.unit


class TestPasswordHashing:
  def test_password_is_hashed(self):
      hashed = pwd_context.hash("mypassword")
      assert hashed != "mypassword"  # not stored in plaintext

  def test_correct_password_verifies(self):
      hashed = pwd_context.hash("mypassword")
      assert pwd_context.verify("mypassword", hashed) == True

  def test_wrong_password_fails(self):
      hashed = pwd_context.hash("mypassword")
      assert pwd_context.verify("wrongpassword", hashed) == False


class TestJWT:
    def test_token_contains_correct_user_id(self):
        access_token = create_access_token(user_id="test_user")
        payload = jwt.decode(access_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        assert payload["sub"] == "test_user"

    def test_invalid_token_raises_error(self):
        access_token = create_access_token(user_id="user")
        invalid_token = access_token + "invalid_str"

        with pytest.raises(JWTError):
            payload = jwt.decode(invalid_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])