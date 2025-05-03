# run.py
from app import create_app
from app.models import db
import os

app = create_app()

# สร้าง CLI command สำหรับสร้าง database
@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database tables created.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)