from NhaKhoa.models.medicine import Medicine
from NhaKhoa.models.medicineType import MedicineType
from NhaKhoa.database.db import get_session


class MedicineDAO:
    # Lấy tất cả thuốc đang hoạt động (status == 0)
    def get_all_medicines(self):
        with get_session() as session:
            medicines = session.query(Medicine).filter(Medicine.status == 0).all()
            for m in medicines:
                m.type_name = m.medicine_type.name if m.medicine_type else "Chưa xác định"
            return medicines

    # Lấy thuốc theo ID (chỉ lấy nếu status == 0)
    def get_by_id(self, medicine_id):
        with get_session() as session:
            medicine = session.query(Medicine) \
                .filter(Medicine.id == medicine_id, Medicine.status == 0) \
                .first()
            if medicine:
                medicine.type_name = medicine.medicine_type.name if medicine.medicine_type else "Chưa xác định"
            return medicine

    # Thêm thuốc mới
    def add_medicine(self, name, type_id, price):
        with get_session() as session:
            new_medicine = Medicine(name=name, medicine_type_id=type_id, price=price)  # status = 0 mặc định
            session.add(new_medicine)
            session.commit()
            new_medicine.type_name = new_medicine.medicine_type.name if new_medicine.medicine_type else "Chưa xác định"
            return new_medicine

    # Cập nhật thuốc
    def update_medicine(self, medicine: Medicine):
        with get_session() as session:
            session.merge(medicine)
            session.commit()

    # XÓA MỀM: đặt status = -1
    def soft_delete(self, id: int):
        with get_session() as session:
            medicine = session.get(Medicine, id)
            if medicine and medicine.status == 0:
                medicine.status = -1
                session.commit()
                return True
            return False

    # Tìm kiếm thuốc (chỉ lấy status == 0)
    def search_medicines(self, keyword: str = "", type_id: int = None):
        with get_session() as session:
            query = session.query(Medicine).filter(Medicine.status == 0).join(MedicineType, isouter=True)
            if keyword:
                keyword = f"%{keyword}%"
                query = query.filter(Medicine.name.ilike(keyword))
            if type_id:
                query = query.filter(Medicine.medicine_type_id == type_id)
            medicines = query.all()
            for m in medicines:
                m.type_name = m.medicine_type.name if m.medicine_type else "Chưa xác định"
            return medicines