class Bill:
    def __init__(self, id=None, appointment_id=None, amount=0, status="Chưa thanh toán", payment_method=None, created_at=None):
        self.id = id
        self.appointment_id = appointment_id
        self.amount = amount
        self.status = status
        self.payment_method = payment_method
        self.created_at = created_at
