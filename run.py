from app import create_app
import os
app = create_app()
if __name__ == '__main__':
    os.makedirs('app/static/uploads/resumes', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)