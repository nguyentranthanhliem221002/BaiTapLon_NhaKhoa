from NhaKhoa.models.status import Status
from NhaKhoa.database.db import get_session

class StatusDAO:
    def get_all(self):
        """Get all statuses"""
        with get_session() as session:
            return session.query(Status).all()

    def get_by_id(self, status_id):
        """Get status by ID"""
        with get_session() as session:
            return session.get(Status, status_id)

    def get_by_name(self, name):
        """Get status by name"""
        with get_session() as session:
            return session.query(Status).filter_by(name=name).first()

    def update(self, status: Status):
        """Update a status"""
        with get_session() as session:
            session.merge(status)
            session.commit()

