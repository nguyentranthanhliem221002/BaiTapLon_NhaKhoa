from flask import flash
from NhaKhoa.models.medicineType import MedicineType
from NhaKhoa.models.medicine import Medicine
from NhaKhoa.database.db import get_session

class MedicineTypeDAO:
    def get_all_medicine_types(self):
        with get_session() as session:
            return session.query(MedicineType).all()

    def get_by_id(self, id):
        with get_session() as session:
            return session.query(MedicineType).filter(MedicineType.id == id).first()

    def add_medicine_type(self, name):
        with get_session() as session:
            new_type = MedicineType(name=name)
            session.add(new_type)
            session.commit()
            flash("Thêm loại thuốc thành công.", "success")
            return new_type

    def update(self, type_obj):
        with get_session() as session:
            session.merge(type_obj)
            session.commit()
            flash("Cập nhật loại thuốc thành công.", "success")

    def delete(self, id):
        with get_session() as session:
            medicines = session.query(Medicine).filter(Medicine.medicine_type_id == id).all()
            if medicines:
                flash("Không thể xóa loại thuốc này vì đang có thuốc liên quan.", "danger")
                return False

            type_obj = session.query(MedicineType).filter(MedicineType.id == id).first()
            if type_obj:
                session.delete(type_obj)
                session.commit()
                flash("Xóa loại thuốc thành công.", "success")
                return True
            else:
                flash("Không tìm thấy loại thuốc.", "warning")
                return False
    def search(self, keyword: str):
        """Tìm loại thuốc theo tên"""
        with get_session() as session:
            return session.query(MedicineType) \
                .filter(MedicineType.name.ilike(f"%{keyword}%")) \
                .all()

    def update(self, type_obj: MedicineType):
        with get_session() as session:
            session.merge(type_obj)
            session.commit()

