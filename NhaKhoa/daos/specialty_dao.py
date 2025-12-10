from NhaKhoa.models.specialty import Specialty
from NhaKhoa.database.db import get_session

class SpecialtyDAO:
    def get_all(self):
        """Get all specialties."""
        with get_session() as session:
            return session.query(Specialty).all()

    def get_by_id(self, id: int):
        """Get a specialty by its ID."""
        with get_session() as session:
            return session.get(Specialty, id)

    def get_name_by_id(self, id: int) -> str:
        """Get the name of a specialty by its ID."""
        with get_session() as session:
            specialty = session.get(Specialty, id)
            return specialty.name if specialty else None

    def add(self, specialty: Specialty):
        """Add a new specialty."""
        with get_session() as session:
            session.add(specialty)
            session.commit()

    def update(self, specialty: Specialty):
        """Update an existing specialty."""
        with get_session() as session:
            session.merge(specialty)
            session.commit()

    def delete(self, id: int):
        """Delete a specialty by its ID."""
        with get_session() as session:
            specialty = session.get(Specialty, id)
            if specialty:
                session.delete(specialty)
                session.commit()

    def search(self, filter_by: str, keyword: str):
        """Search specialties by name or description."""
        with get_session() as session:
            query = session.query(Specialty)
            if filter_by == "name":
                query = query.filter(Specialty.name.ilike(f"%{keyword}%"))
            elif filter_by == "description":
                query = query.filter(Specialty.description.ilike(f"%{keyword}%"))
            return query.all()
