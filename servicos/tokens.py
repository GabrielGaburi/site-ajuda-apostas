"""Tokens assinados e com prazo (confirmação de e-mail, redefinição de senha)."""

from itsdangerous import URLSafeTimedSerializer

from config import SECRET_KEY

serializer = URLSafeTimedSerializer(SECRET_KEY)
