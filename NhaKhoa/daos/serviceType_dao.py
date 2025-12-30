from flask import flash
from NhaKhoa.models.serviceType import ServiceType
from NhaKhoa.models.service import Service
from NhaKhoa.database.db import get_session


class ServiceTypeDAO:
    def get_all_service_types(self):
        with get_session() as session:
            return session.query(ServiceType) \
                .filter(ServiceType.active == True) \
                .all()

    def get_by_id(self, id: int):
        with get_session() as session:
            return session.query(ServiceType) \
                .filter(ServiceType.id == id, ServiceType.active == True) \
                .first()

    def add(self, name: str):
        with get_session() as session:
            service_type = ServiceType(name=name)
            session.add(service_type)
            session.commit()
            return service_type

    def update(self, service_type: ServiceType):
        with get_session() as session:
            session.merge(service_type)
            session.commit()

    def soft_delete(self, id: int):
        with get_session() as session:
            has_service = session.query(Service).filter(
                Service.service_type_id == id,
                Service.active == True
            ).first()

            if has_service:
                flash("Không thể xóa loại dịch vụ này vì vẫn còn dịch vụ thuộc loại này đang hoạt động.", "danger")
                return False

            type_obj = session.query(ServiceType).filter(ServiceType.id == id).first()
            if type_obj and type_obj.active == True:
                type_obj.active = False
                session.commit()
                flash("Xóa loại dịch vụ thành công! (Đã ẩn khỏi hệ thống)", "success")
                return True
            else:
                flash("Không tìm thấy loại dịch vụ hoặc đã bị xóa trước đó!", "warning")
                return False

    def search(self, keyword: str):
        with get_session() as session:
            return session.query(ServiceType) \
                .filter(
                    ServiceType.active == True,
                    ServiceType.name.ilike(f"%{keyword}%")
                ) \
                .all()