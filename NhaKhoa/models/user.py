class User:
    def __init__(self, id=None, username="", password="", role="patient", email="", reset_token=None, reset_token_expiry=None):
        self.id = id
        self.username = username
        self.password = password
        self.role = role  # patient / doctor / admin
        self.email = email
        self.reset_token = reset_token
        self.reset_token_expiry = reset_token_expiry
