from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import imghdr
import magic # type: ignore

media = Blueprint('media', __name__)

# Configuration
UPLOAD_FOLDER = 'static/images'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_type(file):
    # Read a small portion of the file for MIME type detection
    file_content = file.read(1024)
    file.seek(0)  # Reset file pointer after reading
    
    # Check MIME type
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(file_content)
    
    # For images, also validate using imghdr
    if file_type.startswith('image/'):
        file_content = file.read(1024)
        file.seek(0)
        image_type = imghdr.what(None, file_content)
        if not image_type:
            return False
    
    return file_type in {
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }

@media.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check file size limit
        if request.content_length > MAX_CONTENT_LENGTH:
            return jsonify({'error': 'File too large'}), 413
        
        # Check if file part exists
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Validate file content
        if not validate_file_type(file):
            return jsonify({'error': 'Invalid file content'}), 400
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        final_filename = f"{timestamp}{filename}"
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        file_path = os.path.join(UPLOAD_FOLDER, final_filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': final_filename,
            'filepath': file_path
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500