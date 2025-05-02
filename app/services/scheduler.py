# app/services/scheduler.py
from flask import current_app
from app.services.cleanup_service import cleanup_import_files, cleanup_temp_import_files
import atexit
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


def init_scheduler(app):
    """
    เริ่มต้น scheduler สำหรับงานที่ต้องทำเป็นประจำ

    - ทำความสะอาดไฟล์ import ทุกวัน (เก็บแค่ 3 ไฟล์ล่าสุด)
    - ทำความสะอาดไฟล์ชั่วคราวที่เก่ากว่า 24 ชั่วโมงทุก 6 ชั่วโมง
    """
    with app.app_context():
        scheduler = BackgroundScheduler()

        # เพิ่มงานทำความสะอาดไฟล์ import ทุกวัน
        scheduler.add_job(
            func=lambda: cleanup_import_files(max_files=3),
            trigger=IntervalTrigger(hours=24),
            id='cleanup_import_files',
            name='Clean up import files',
            replace_existing=True
        )

        # เพิ่มงานทำความสะอาดไฟล์ชั่วคราวทุก 6 ชั่วโมง
        scheduler.add_job(
            func=lambda: cleanup_temp_import_files(hours=24),
            trigger=IntervalTrigger(hours=6),
            id='cleanup_temp_files',
            name='Clean up temporary files',
            replace_existing=True
        )

        # เริ่มต้น scheduler
        scheduler.start()
        app.logger.info('Scheduler started for file cleanup tasks')

        # ให้ scheduler หยุดทำงานเมื่อแอปปิด
        atexit.register(lambda: scheduler.shutdown())