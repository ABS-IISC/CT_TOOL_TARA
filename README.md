# CT Review Tool - Hawkeye AI Analysis

A deployable web application that converts the original Jupyter notebook-based CT review tool into a modern web interface with all the same functionality.

## Features

### Core Functionality (Preserved from Original)
- **Document Upload**: Upload Word documents (.docx) for analysis
- **Section-based Analysis**: Automatically extracts and analyzes document sections
- **Hawkeye Framework**: 20-point investigation checklist integration
- **AI-Powered Feedback**: AWS Bedrock integration for intelligent analysis
- **Risk Classification**: High/Medium/Low risk assessment
- **Interactive Review**: Accept/reject feedback with comments
- **Custom Feedback**: Add user-defined feedback items
- **AI Chat Assistant**: Ask questions about feedback and guidelines
- **Document Generation**: Export reviewed documents with embedded comments
- **Progress Tracking**: Real-time statistics and progress monitoring

### New Web Interface Features
- **Modern UI**: Bootstrap-based responsive design
- **Drag & Drop Upload**: Easy file upload with visual feedback
- **Split-Screen Layout**: Document view alongside feedback panel
- **Tabbed Interface**: Separate tabs for feedback and chat
- **Real-time Updates**: Live statistics and progress tracking
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices
- **Status Logging**: Comprehensive activity logging
- **Download Management**: Direct download of reviewed documents

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the project files**
   ```bash
   cd ct_review_tool_12
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up AWS credentials (if using real AWS Bedrock)**
   - Configure AWS CLI or set environment variables
   - Ensure proper IAM permissions for Bedrock access

4. **Add guideline documents (optional)**
   - Place `CT_EE_Review_Guidelines.docx` in the root directory
   - Place `Hawkeye_checklist.docx` in the root directory

## Running the Application

### Development Mode
```bash
python run.py
```

### Production Mode
```bash
python run.py production
```

The application will be available at: `http://localhost:5000`

## Usage

### 1. Upload Document
- Click "Choose File" or drag and drop a Word document (.docx)
- The system will process and extract sections automatically

### 2. Review Sections
- Navigate through sections using the dropdown or Previous/Next buttons
- View original document content on the left panel
- Review AI-generated feedback on the right panel

### 3. Manage Feedback
- **Accept**: Click ✓ Accept to include feedback as document comments
- **Reject**: Click ✗ Reject to dismiss feedback
- **Add Custom**: Use the form to add your own feedback items

### 4. AI Chat Assistant
- Switch to the "AI Chat" tab
- Ask questions about feedback, Hawkeye guidelines, or document content
- Get contextual responses based on current section

### 5. Complete Review
- Click "Complete Review" when finished
- Download the reviewed document with embedded comments
- Open in Microsoft Word to see comments in the margin

## File Structure

```
ct_review_tool_12/
├── app.py                 # Main Flask application
├── run.py                 # Deployment script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main web interface
├── uploads/              # Uploaded documents (created automatically)
├── outputs/              # Generated reviewed documents (created automatically)
├── CT_EE_Review_Guidelines.docx  # Guidelines document (optional)
└── Hawkeye_checklist.docx       # Hawkeye checklist (optional)
```

## Key Components

### Backend (app.py)
- **Flask Routes**: Handle file upload, analysis, feedback management
- **Document Processing**: Extract sections from Word documents
- **AI Integration**: AWS Bedrock for intelligent analysis (with fallback)
- **Comment Generation**: Create Word documents with embedded comments
- **Session Management**: Track user sessions and document state

### Frontend (templates/index.html)
- **Responsive Design**: Bootstrap 5 with custom styling
- **Interactive Elements**: File upload, section navigation, feedback management
- **Real-time Updates**: AJAX calls for seamless user experience
- **Chat Interface**: AI assistant integration
- **Progress Tracking**: Visual progress indicators and statistics

### Core Classes
- **ReviewSession**: Manages document review state
- **WordDocumentWithComments**: Handles Word document comment insertion

## Configuration

### Environment Variables
- `FLASK_ENV`: Set to 'production' for production deployment
- `AWS_ACCESS_KEY_ID`: AWS credentials (if using real Bedrock)
- `AWS_SECRET_ACCESS_KEY`: AWS credentials (if using real Bedrock)
- `AWS_DEFAULT_REGION`: AWS region for Bedrock

### Application Settings
- **Upload folder**: `uploads/` (configurable in app.py)
- **Output folder**: `outputs/` (configurable in app.py)
- **Max file size**: Default Flask limits apply
- **Allowed extensions**: `.docx` only

## Deployment Options

### Local Development
- Run with `python run.py`
- Debug mode enabled for development

### Production Deployment
- Run with `python run.py production`
- Consider using WSGI server (Gunicorn, uWSGI)
- Set up reverse proxy (Nginx, Apache)
- Configure SSL/HTTPS for security

### Docker Deployment (Optional)
Create a Dockerfile:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py", "production"]
```

## Security Considerations

- **File Upload**: Only .docx files are accepted
- **Session Management**: Uses Flask sessions with secret key
- **Input Validation**: All user inputs are validated
- **AWS Credentials**: Store securely, never in code
- **HTTPS**: Use SSL/TLS in production
- **File Cleanup**: Temporary files are cleaned up automatically

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

2. **AWS Bedrock Errors**
   - Check AWS credentials and permissions
   - The app includes fallback mock responses for testing

3. **File Upload Issues**
   - Ensure `uploads/` directory exists and is writable
   - Check file size limits

4. **Document Processing Errors**
   - Verify the uploaded file is a valid .docx document
   - Check for corrupted files

### Debug Mode
Run in development mode to see detailed error messages:
```bash
python run.py
```

## Differences from Original Jupyter Notebook

### Preserved Functionality
- ✅ All core document analysis features
- ✅ Hawkeye framework integration
- ✅ AI feedback generation
- ✅ Risk classification
- ✅ Custom feedback addition
- ✅ Chat assistant
- ✅ Document comment generation
- ✅ Progress tracking

### Improvements
- 🆕 Modern web interface
- 🆕 Responsive design
- 🆕 Better user experience
- 🆕 Session management
- 🆕 Real-time updates
- 🆕 Drag & drop upload
- 🆕 Mobile compatibility
- 🆕 Production deployment ready

### Technical Changes
- **Framework**: Jupyter widgets → Flask web application
- **UI**: ipywidgets → Bootstrap HTML/CSS/JavaScript
- **State Management**: Global variables → Session-based storage
- **File Handling**: Direct file access → Upload/download system
- **Deployment**: Notebook environment → Standalone web server

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the Flask and Python documentation
3. Verify AWS Bedrock setup if using real AI integration
4. Check browser console for JavaScript errors

## License

This tool maintains the same functionality as the original Jupyter notebook implementation while providing a modern, deployable web interface.