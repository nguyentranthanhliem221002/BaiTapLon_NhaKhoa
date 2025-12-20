from flask import flash
from NhaKhoa.models.medicineType import MedicineType
from NhaKhoa.models.medicine import Medicine
from NhaKhoa.database.db import get_session

class MedicineTypeDAO:
    # Lấy tất cả loại thuốc đang hoạt động
    def get_all_medicine_types(self):
        with get_session() as session:
            return session.query(MedicineType) \
                .filter(MedicineType.active == True) \
                .all()

    def get_by_id(self, id: int):
        with get_session() as session:
            return session.query(MedicineType) \
                .filter(MedicineType.id == id, MedicineType.active == True) \
                .first()

    # Thêm loại thuốc mới
    def add_medicine_type(self, name: str):
        with get_session() as session:
            new_type = MedicineType(name=name)  # status = 0 mặc định
            session.add(new_type)
            session.commit()
            return new_type

    # Cập nhật loại thuốc
    def update(self, type_obj: MedicineType):
        with get_session() as session:
            session.merge(type_obj)
            session.commit()

    def soft_delete(self, id: int):
        with get_session() as session:
            has_medicine = session.query(Medicine).filter(
                Medicine.medicine_type_id == id,
                Medicine.active == True
            ).first()

            if has_medicine:
                flash("Không thể xóa loại thuốc này vì vẫn còn thuốc thuộc loại này đang hoạt động.", "danger")
                return False

            type_obj = session.query(MedicineType).filter(MedicineType.id == id).first()
            if type_obj and type_obj.active == True:
                type_obj.active = False
                session.commit()
                flash("Xóa loại thuốc thành công! (Đã ẩn khỏi hệ thống)", "success")
                return True
            else:
                flash("Không tìm thấy loại thuốc hoặc đã bị xóa trước đó!", "warning")
                return False