from NhaKhoa.models.service import Service
from NhaKhoa.models.serviceType import ServiceType
from NhaKhoa.database.db import get_session


class ServiceDAO:
    def get_all_services(self):
        with get_session() as session:
            services = session.query(Service).filter(Service.status == 0).all()
            for s in services:
                s.type_name = s.service_type.name if s.service_type else "Chưa xác định"
            return services

    def get_service_by_id(self, id: int):
        with get_session() as session:
            service = session.query(Service) \
                .filter(Service.id == id, Service.status == 0) \
                .first()
            if service:
                service.type_name = service.service_type.name if service.service_type else "Chưa xác định"
            return service

    def add_service(self, name: str, type_id: int, price: float):
        with get_session() as session:
            svc = Service(name=name, service_type_id=type_id, price=price)  # status tự động = 0
            session.add(svc)
            session.commit()
            svc.type_name = svc.service_type.name if svc.service_type else "Chưa xác định"
            return svc

    def update_service(self, service: Service):
        with get_session() as session:
            session.merge(service)
            session.commit()

    def soft_delete(self, id: int):
        with get_session() as session:
            service = session.get(Service, id)
            if service and service.status == 0:
                service.status = -1
                session.commit()
                return True
            return False

    def restore(self, id: int):
        with get_session() as session:
            service = session.get(Service, id)
            if service and service.status == -1:
                service.status = 0
                session.commit()
                return True
            return False

    def add_service_type(self, name: str):
        with get_session() as session:
            type_obj = ServiceType(name=name)
            session.add(type_obj)
            session.commit()
            return type_obj

    def search(self, filter_by: str, keyword: str):
        with get_session() as session:
            query = session.query(Service).filter(Service.status == 0)
            if filter_by == "name":
                query = query.filter(Service.name.ilike(f"%{keyword}%"))
            elif filter_by == "type":
                query = query.join(Service.service_type).filter(ServiceType.name.ilike(f"%{keyword}%"))
            return query.all()

    def get_services_by_type(self, type_id: int):
        with get_session() as session:
            return session.query(Service) \
                .filter(
                    Service.service_type_id == type_id,
                    Service.status == 0
                ).all()