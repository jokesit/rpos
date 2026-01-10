import sys
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

def compress_image(image_field, max_size=(800, 800)):
    """
    ฟังก์ชันสำหรับย่อขนาดรูปภาพและลดคุณภาพไฟล์เล็กน้อยเพื่อประหยัดพื้นที่
    :param image_field: field รูปภาพจาก model
    :param max_size: ขนาดสูงสุด (กว้าง, สูง) ที่ต้องการ (default 800x800)
    """
    # ถ้าไม่มีรูปภาพส่งมา ให้ข้ามไปเลย
    if not image_field:
        return None

    # เปิดรูปภาพด้วย Pillow
    im = Image.open(image_field)

    # ถ้าเป็นรูป PNG (มีพื้นหลังใส) ต้องแปลงโหมดเป็น RGBA ก่อน (กันเหนียว)
    # ถ้าเป็น JPEG จะเป็น RGB
    if im.mode != 'RGB' and im.format == 'JPEG':
        im = im.convert('RGB')

    # คำนวณและย่อขนาดภาพ (thumbnail จะรักษาสัดส่วนภาพให้เอง ไม่เบี้ยว)
    im.thumbnail(max_size, Image.Resampling.LANCZOS)

    # เตรียม Buffer ในหน่วยความจำเพื่อบันทึกรูปใหม่
    output = BytesIO()

    # ตรวจสอบนามสกุลไฟล์เพื่อบันทึกให้ถูก Format
    if im.format == 'PNG':
        im.save(output, format='PNG', optimize=True)
    elif im.format == 'GIF':
        im.save(output, format='GIF', optimize=True)
    else:
        # กรณีทั่วไป (JPEG) บันทึกเป็น JPEG และลด Quality เหลือ 85% (ตาเปล่าแยกไม่ออก แต่ไฟล์เล็กลงมาก)
        im.save(output, format='JPEG', quality=85)

    output.seek(0)

    # สร้าง InMemoryUploadedFile ใหม่เพื่อส่งกลับไปบันทึก
    return InMemoryUploadedFile(
        output,
        'ImageField',
        "%s.%s" % (image_field.name.split('.')[0], im.format.lower()),
        "image/%s" % im.format.lower(),
        sys.getsizeof(output),
        None
    )