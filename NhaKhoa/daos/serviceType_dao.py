from NhaKhoa.models.serviceType import ServiceType
from NhaKhoa.database.db import get_session

class ServiceTypeDAO:
    def get_all_service_types(self):
        with get_session() as session:
            return session.query(ServiceType).all()

    def get_by_id(self, id: int):
        with get_session() as session:
            return session.get(ServiceType, id)

    def add(self, name: str):
        with get_session() as session:
            service_type = ServiceType(name=name)
            session.add(service_type)
            session.commit()  # commit bắt buộc

    def update(self, service_type: ServiceType):
        with get_session() as session:
            session.merge(service_type)  # merge để update object detached
            session.commit()

    def delete(self, service_type: ServiceType):
        with get_session() as session:
            session.delete(service_type)
            session.commit()
    def search(self, keyword: str):
        with get_session() as session:
            return session.query(ServiceType) \
                .filter(ServiceType.name.ilike(f"%{keyword}%")) \
                .all()

    def update(self, service_type: ServiceType):
        with get_session() as session:
            session.merge(service_type)
            session.commit()
