from NhaKhoa.models.medicine import Medicine
from NhaKhoa.models.medicineType import MedicineType
from NhaKhoa.database.db import get_session

class MedicineDAO:
    def get_all_medicines(self):
        with get_session() as session:
            medicines = session.query(Medicine).all()
            for m in medicines:
                m.type_name = m.medicine_type.name if m.medicine_type else "Chưa xác định"
            return medicines

    def get_by_id(self, medicine_id):
        with get_session() as session:
            medicine = session.query(Medicine).filter(Medicine.id == medicine_id).first()
            if medicine:
                medicine.type_name = medicine.medicine_type.name if medicine.medicine_type else "Chưa xác định"
            return medicine

    def add_medicine(self, name, type_id, price):
        with get_session() as session:
            new_medicine = Medicine(name=name, medicine_type_id=type_id, price=price)
            session.add(new_medicine)
            session.commit()
            return new_medicine

    def update_medicine(self, medicine: Medicine):
        with get_session() as session:
            session.merge(medicine)
            session.commit()

    def search_medicines(self, keyword: str = "", type_id: int = None):
        with get_session() as session:
            query = session.query(Medicine).join(MedicineType, isouter=True)
            if keyword:
                keyword = f"%{keyword}%"
                query = query.filter(Medicine.name.ilike(keyword))
            if type_id:
                query = query.filter(Medicine.medicine_type_id == type_id)
            medicines = query.all()
            for m in medicines:
                m.type_name = m.medicine_type.name if m.medicine_type else "Chưa xác định"
            return medicines

