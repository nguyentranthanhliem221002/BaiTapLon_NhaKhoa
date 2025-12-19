from flask import flash
from NhaKhoa.models.serviceType import ServiceType
from NhaKhoa.models.service import Service
from NhaKhoa.database.db import get_session


class ServiceTypeDAO:
    # Lấy tất cả loại dịch vụ đang hoạt động (status == 0)
    def get_all_service_types(self):
        with get_session() as session:
            return session.query(ServiceType) \
                .filter(ServiceType.status == 0) \
                .all()

    # Lấy theo ID, chỉ lấy nếu status == 0
    def get_by_id(self, id: int):
        with get_session() as session:
            return session.query(ServiceType) \
                .filter(ServiceType.id == id, ServiceType.status == 0) \
                .first()

    # Thêm loại dịch vụ mới (status mặc định = 0 từ model)
    def add(self, name: str):
        with get_session() as session:
            service_type = ServiceType(name=name)  # status tự động = 0
            session.add(service_type)
            session.commit()
            return service_type

    # Cập nhật loại dịch vụ
    def update(self, service_type: ServiceType):
        with get_session() as session:
            session.merge(service_type)
            session.commit()

    # XÓA MỀM: kiểm tra ràng buộc + đặt status = -1
    def soft_delete(self, id: int):
        with get_session() as session:
            # Kiểm tra còn dịch vụ nào thuộc loại này và đang hoạt động không
            has_service = session.query(Service).filter(
                Service.service_type_id == id,
                Service.status == 0  # chỉ kiểm tra dịch vụ đang hoạt động
            ).first()

            if has_service:
                flash("Không thể xóa loại dịch vụ này vì vẫn còn dịch vụ thuộc loại này đang hoạt động.", "danger")
                return False

            type_obj = session.query(ServiceType).filter(ServiceType.id == id).first()
            if type_obj and type_obj.status == 0:
                type_obj.status = -1
                session.commit()
                flash("Xóa loại dịch vụ thành công! (Đã ẩn khỏi hệ thống)", "success")
                return True
            else:
                flash("Không tìm thấy loại dịch vụ hoặc đã bị xóa trước đó!", "warning")
                return False

    # Tìm kiếm loại dịch vụ (chỉ lấy status == 0)
    def search(self, keyword: str):
        with get_session() as session:
            return session.query(ServiceType) \
                .filter(
                    ServiceType.status == 0,
                    ServiceType.name.ilike(f"%{keyword}%")
                ) \
                .all()