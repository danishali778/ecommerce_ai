from unittest.mock import Mock

from app.services.auth import AuthService


def test_register_delegates_to_module():
    db = Mock()
    module = Mock()
    module.register.return_value = {"access_token": "access"}
    service = AuthService(db=db, module=module)

    payload = Mock()
    result = service.register(payload)

    assert result["access_token"] == "access"
    module.register.assert_called_once_with(payload)
