from flask import Flask, render_template, request, jsonify, send_file, session
import pandas as pd
import base64
import json
from datetime import datetime
import boto3
import threading
import os
import re
import traceback
import time
from pathlib import Path
import asyncio
import uuid
from collections import defaultdict
import queue
import zipfile
import shutil
from lxml import etree
from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'docx'}

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global variables
guidelines_content = None
hawkeye_checklist = None
document_sessions = {}

# Define paths to guidelines documents
GUIDELINES_PATH = "CT_EE_Review_Guidelines.docx"
HAWKEYE_PATH = "Hawkeye_checklist.docx"

# Hawkeye checklist mapping
HAWKEYE_SECTIONS = {
    1: "Initial Assessment",
    2: "Investigation Process", 
    3: "Seller Classification",
    4: "Enforcement Decision-Making",
    5: "Additional Verification (High-Risk Cases)",
    6: "Multiple Appeals Handling",
    7: "Account Hijacking Prevention",
    8: "Funds Management",
    9: "REs-Q Outreach Process",
    10: "Sentiment Analysis",
    11: "Root Cause Analysis",
    12: "Preventative Actions",
    13: "Documentation and Reporting",
    14: "Cross-Team Collaboration",
    15: "Quality Control",
    16: "Continuous Improvement",
    17: "Communication Standards",
    18: "Performance Metrics",
    19: "Legal and Compliance",
    20: "New Service Launch Considerations"
}

# Standard writeup sections to look for
STANDARD_SECTIONS = [
    "Executive Summary",
    "Background",
    "Resolving Actions",
    "Root Cause",
    "Preventative Actions",
    "Investigation Process",
    "Seller Classification",
    "Documentation and Reporting",
    "Impact Assessment",
    "Timeline",
    "Recommendations"
]

# Sections to exclude from analysis
EXCLUDED_SECTIONS = [
    "Original Email",
    "Email Correspondence",
    "Raw Data",
    "Logs",
    "Attachments"
]

class WordDocumentWithComments:
    """Helper class to add comments to Word documents"""
    
    def __init__(self, doc_path):
        self.doc_path = doc_path
        self.temp_dir = f"temp_{uuid.uuid4()}"
        self.comments = []
        self.comment_id = 1
        
    def add_comment(self, paragraph_index, comment_text, author="AI Feedback"):
        """Add a comment to be inserted later"""
        self.comments.append({
            'id': self.comment_id,
            'paragraph_index': paragraph_index,
            'text': comment_text,
            'author': author,
            'date': datetime.now()
        })
        self.comment_id += 1
    
    def _create_comment_xml(self, comment):
        """Create comment XML structure"""
        comment_xml = f'''
        <w:comment w:id="{comment['id']}" w:author="{comment['author']}" 
                   w:date="{comment['date'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')}" 
                   xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:p>
                <w:r>
                    <w:t>{comment['text']}</w:t>
                </w:r>
            </w:p>
        </w:comment>
        '''
        return comment_xml
    
    def save_with_comments(self, output_path):
        """Save document with comments added"""
        try:
            doc = Document(self.doc_path)
            temp_docx = f"{self.temp_dir}_temp.docx"
            doc.save(temp_docx)
            
            os.makedirs(self.temp_dir, exist_ok=True)
            with zipfile.ZipFile(temp_docx, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            comments_path = os.path.join(self.temp_dir, 'word', 'comments.xml')
            
            comments_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            '''
            
            for comment in self.comments:
                comments_xml += self._create_comment_xml(comment)
            
            comments_xml += '</w:comments>'
            
            with open(comments_path, 'w', encoding='utf-8') as f:
                f.write(comments_xml)
            
            rels_path = os.path.join(self.temp_dir, 'word', '_rels', 'document.xml.rels')
            if os.path.exists(rels_path):
                with open(rels_path, 'r', encoding='utf-8') as f:
                    rels_content = f.read()
                
                if 'comments.xml' not in rels_content:
                    new_rel = '<Relationship Id="rIdComments" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>'
                    rels_content = rels_content.replace('</Relationships>', f'{new_rel}</Relationships>')
                    
                    with open(rels_path, 'w', encoding='utf-8') as f:
                        f.write(rels_content)
            
            content_types_path = os.path.join(self.temp_dir, '[Content_Types].xml')
            if os.path.exists(content_types_path):
                with open(content_types_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'comments.xml' not in content:
                    new_type = '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
                    content = content.replace('</Types>', f'{new_type}</Types>')
                    
                    with open(content_types_path, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.temp_dir)
                        zipf.write(file_path, arcname)
            
            shutil.rmtree(self.temp_dir)
            os.remove(temp_docx)
            
            return True
            
        except Exception as e:
            print(f"Error adding comments: {str(e)}")
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            if os.path.exists(temp_docx):
                os.remove(temp_docx)
            return False

class ReviewSession:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.document_name = ""
        self.document_content = ""
        self.document_object = None
        self.document_path = ""
        self.sections = {}
        self.section_paragraphs = {}
        self.paragraph_indices = {}
        self.current_section = 0
        self.feedback_history = defaultdict(list)
        self.section_status = {}
        self.accepted_feedback = defaultdict(list)
        self.rejected_feedback = defaultdict(list)
        self.user_feedback = defaultdict(list)
        self.ai_feedback_cache = {}
        self.document_comments = []
        self.chat_history = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_guidelines():
    """Load the CT EE Review guidelines and Hawkeye checklist"""
    global guidelines_content, hawkeye_checklist
    
    try:
        if os.path.exists(GUIDELINES_PATH):
            guidelines_content = read_docx(GUIDELINES_PATH)
        
        if os.path.exists(HAWKEYE_PATH):
            hawkeye_checklist = read_docx(HAWKEYE_PATH)
        
        return guidelines_content, hawkeye_checklist
    except Exception as e:
        return None, None

def read_docx(file_path):
    """Extract text from a Word document"""
    try:
        doc = Document(file_path)
        full_text = []
        
        for para in doc.paragraphs:
            full_text.append(para.text)
            
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    full_text.append(cell.text)
                    
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error reading document: {str(e)}"

def extract_document_sections_from_docx(doc):
    """Extract sections from Word document based on bold formatting"""
    sections = {}
    section_paragraphs = {}
    paragraph_indices = {}
    current_section = None
    current_content = []
    current_paragraphs = []
    current_indices = []
    
    for idx, para in enumerate(doc.paragraphs):
        is_bold = False
        if para.runs:
            bold_runs = sum(1 for run in para.runs if run.bold)
            total_runs = len(para.runs)
            is_bold = bold_runs > total_runs / 2
        
        text = para.text.strip()
        is_section_header = False
        
        if is_bold and text and len(text) < 100:
            for std_section in STANDARD_SECTIONS:
                if std_section.lower() in text.lower():
                    is_section_header = True
                    break
            
            if not is_section_header and (text.endswith(':') or text.isupper()):
                is_section_header = True
        
        if is_section_header:
            if current_section and current_content:
                exclude = False
                for excluded in EXCLUDED_SECTIONS:
                    if excluded.lower() in current_section.lower():
                        exclude = True
                        break
                
                if not exclude:
                    sections[current_section] = '\n'.join(current_content)
                    section_paragraphs[current_section] = current_paragraphs
                    paragraph_indices[current_section] = current_indices
            
            current_section = text.rstrip(':')
            current_content = []
            current_paragraphs = []
            current_indices = []
        else:
            if text:
                current_content.append(text)
                current_paragraphs.append(para)
                current_indices.append(idx)
    
    if current_section and current_content:
        exclude = False
        for excluded in EXCLUDED_SECTIONS:
            if excluded.lower() in current_section.lower():
                exclude = True
                break
        
        if not exclude:
            sections[current_section] = '\n'.join(current_content)
            section_paragraphs[current_section] = current_paragraphs
            paragraph_indices[current_section] = current_indices
    
    if not sections:
        all_text = []
        all_paras = []
        all_indices = []
        for idx, para in enumerate(doc.paragraphs):
            if para.text.strip():
                all_text.append(para.text)
                all_paras.append(para)
                all_indices.append(idx)
        sections = {"Main Content": '\n'.join(all_text)}
        section_paragraphs = {"Main Content": all_paras}
        paragraph_indices = {"Main Content": all_indices}
    
    return sections, section_paragraphs, paragraph_indices

def get_hawkeye_reference(category, content):
    """Map feedback to relevant Hawkeye checklist items"""
    references = []
    
    keyword_mapping = {
        1: ["customer experience", "cx impact", "customer trust", "buyer impact"],
        2: ["investigation", "sop", "enforcement decision", "abuse pattern"],
        3: ["seller classification", "good actor", "bad actor", "confused actor"],
        4: ["enforcement", "violation", "warning", "suspension"],
        5: ["verification", "supplier", "authenticity", "documentation"],
        6: ["appeal", "repeat", "retrospective"],
        7: ["hijacking", "security", "authentication", "secondary user"],
        8: ["funds", "disbursement", "financial"],
        9: ["outreach", "communication", "clarification"],
        10: ["sentiment", "escalation", "health safety", "legal threat"],
        11: ["root cause", "process gap", "system failure"],
        12: ["preventative", "solution", "improvement", "mitigation"],
        13: ["documentation", "reporting", "background"],
        14: ["cross-team", "collaboration", "engagement"],
        15: ["quality", "audit", "review", "performance"],
        16: ["continuous improvement", "training", "update"],
        17: ["communication standard", "messaging", "clarity"],
        18: ["metrics", "tracking", "measurement"],
        19: ["legal", "compliance", "regulation"],
        20: ["launch", "pilot", "rollback"]
    }
    
    content_lower = content.lower()
    category_lower = category.lower()
    
    for section_num, keywords in keyword_mapping.items():
        for keyword in keywords:
            if keyword in content_lower or keyword in category_lower:
                references.append({
                    'number': section_num,
                    'name': HAWKEYE_SECTIONS[section_num]
                })
                break
    
    return references[:3]

def classify_risk_level(feedback_item):
    """Classify risk level based on Hawkeye criteria"""
    high_risk_indicators = [
        "counterfeit", "fraud", "manipulation", "multiple violation",
        "immediate action", "legal", "health safety", "bad actor"
    ]
    
    medium_risk_indicators = [
        "pattern", "violation", "enforcement", "remediation",
        "correction", "warning"
    ]
    
    content_lower = f"{feedback_item.get('description', '')} {feedback_item.get('category', '')}".lower()
    
    for indicator in high_risk_indicators:
        if indicator in content_lower:
            return "High"
    
    for indicator in medium_risk_indicators:
        if indicator in content_lower:
            return "Medium"
    
    return "Low"

def invoke_aws_semantic_search(system_prompt, user_prompt, operation_name="LLM Analysis"):
    """AWS Bedrock invocation with Hawkeye guidelines"""
    global guidelines_content, hawkeye_checklist
    
    if guidelines_content is None or hawkeye_checklist is None:
        guidelines_content, hawkeye_checklist = load_guidelines()
    
    enhanced_system_prompt = system_prompt
    if hawkeye_checklist:
        truncated_hawkeye = hawkeye_checklist[:30000]
        enhanced_system_prompt = f"""{system_prompt}

HAWKEYE INVESTIGATION CHECKLIST:
{truncated_hawkeye}

Apply these Hawkeye investigation mental models in your analysis. Reference specific checklist items when providing feedback."""
    
    try:
        runtime = boto3.client('bedrock-runtime')
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "system": enhanced_system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        })
        
        response = runtime.invoke_model(
            body=body,
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        # Return mock data for testing
        time.sleep(1)
        if "chat" in operation_name.lower():
            return "Based on the Hawkeye guidelines, I can help you understand the feedback better. The 20-point checklist emphasizes thorough investigation and customer impact assessment. What specific aspect would you like me to clarify?"
        
        return json.dumps({
            "feedback_items": [
                {
                    "id": "1",
                    "type": "critical",
                    "category": "investigation process",
                    "description": "Missing evaluation of customer experience (CX) impact. How might this abuse affect customer trust and satisfaction?",
                    "suggestion": "Add analysis of potential negative reviews, returns, or complaints that could result from this issue",
                    "example": "Consider both immediate and long-term effects on customer trust as outlined in Hawkeye #1",
                    "questions": [
                        "Have you evaluated the customer experience (CX) impact?",
                        "Did you consider how this affects buyer trust?"
                    ],
                    "confidence": 0.95
                },
                {
                    "id": "2",
                    "type": "important",
                    "category": "root cause analysis",
                    "description": "Root cause analysis lacks identification of process gaps that allowed this issue",
                    "suggestion": "Include analysis of weaknesses in current procedures and suggest improvements",
                    "example": "Reference the case study about ex-Amazon employee account compromise",
                    "questions": [
                        "What process gaps allowed this issue to occur?",
                        "Are there system failures that contributed?"
                    ],
                    "confidence": 0.85
                }
            ]
        })

def analyze_section_with_ai(section_name, section_content, doc_type="Full Write-up"):
    """Analyze a single section with Hawkeye framework"""
    
    prompt = f"""Analyze this section "{section_name}" from a {doc_type} document using the Hawkeye investigation framework.

SECTION CONTENT:
{section_content[:3000]}

Provide feedback following the 20-point Hawkeye checklist. For each feedback item, include:
1. Specific questions from the Hawkeye checklist that should be addressed
2. References to relevant Hawkeye checkpoint numbers (#1-20)
3. Examples from the case studies when applicable
4. Risk classification (High/Medium/Low)

Return feedback in this JSON format:
{{
    "feedback_items": [
        {{
            "id": "unique_id",
            "type": "critical|important|suggestion|positive",
            "category": "category matching Hawkeye sections",
            "description": "Clear description referencing Hawkeye criteria",
            "suggestion": "Specific suggestion based on Hawkeye guidelines",
            "example": "Example from case studies or Hawkeye checklist",
            "questions": ["Question 1 from Hawkeye?", "Question 2?"],
            "hawkeye_refs": [1, 11, 12],
            "risk_level": "High|Medium|Low",
            "confidence": 0.95
        }}
    ]
}}"""
    
    system_prompt = "You are an expert document reviewer following the Hawkeye investigation mental models for CT EE guidelines."
    
    response = invoke_aws_semantic_search(system_prompt, prompt, f"Hawkeye Analysis: {section_name}")
    
    try:
        result = json.loads(response)
    except:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
            except:
                result = {"feedback_items": []}
        else:
            result = {"feedback_items": []}
    
    for item in result.get('feedback_items', []):
        if 'hawkeye_refs' not in item:
            refs = get_hawkeye_reference(item.get('category', ''), item.get('description', ''))
            item['hawkeye_refs'] = [ref['number'] for ref in refs]
        
        if 'risk_level' not in item:
            item['risk_level'] = classify_risk_level(item)
    
    return result

def process_chat_query(query, context, session_id):
    """Process chat query with context awareness"""
    session = document_sessions.get(session_id)
    if not session:
        return "No active session found."
    
    context_info = f"""
    Current Section: {context.get('current_section', 'None')}
    Document Type: Full Write-up
    """
    
    prompt = f"""You are an AI assistant helping with document review using the Hawkeye framework.

CONTEXT:
{context_info}

HAWKEYE GUIDELINES REFERENCE:
The 20-point Hawkeye checklist includes:
1. Initial Assessment - Evaluate CX impact
2. Investigation Process - Challenge SOPs
3. Seller Classification - Identify good/bad actors
4. Enforcement Decision-Making
5. Additional Verification for High-Risk Cases
...and 15 more points

USER QUESTION: {query}

Provide a helpful, specific response that references the Hawkeye guidelines when relevant. Be concise but thorough."""
    
    system_prompt = "You are an expert assistant for the Hawkeye document review system."
    
    response = invoke_aws_semantic_search(system_prompt, prompt, "Chat Assistant")
    
    return response

def create_reviewed_document_with_proper_comments(original_doc_path, doc_name, comments_data):
    """Create a copy of the original document with proper Word comments"""
    
    try:
        doc_with_comments = WordDocumentWithComments(original_doc_path)
        
        for comment_data in comments_data:
            author = comment_data.get('author', 'AI Feedback')
            doc_with_comments.add_comment(
                paragraph_index=comment_data['paragraph_index'],
                comment_text=comment_data['comment'],
                author=author
            )
        
        output_path = os.path.join(OUTPUT_FOLDER, f'reviewed_{doc_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx')
        success = doc_with_comments.save_with_comments(output_path)
        
        if success:
            return output_path
        else:
            return create_simple_reviewed_copy(original_doc_path, doc_name, comments_data)
            
    except Exception as e:
        print(f"Error creating document with comments: {str(e)}")
        return create_simple_reviewed_copy(original_doc_path, doc_name, comments_data)

def create_simple_reviewed_copy(original_doc_path, doc_name, comments_data):
    """Create a simple copy with inline comment markers as fallback"""
    try:
        output_path = os.path.join(OUTPUT_FOLDER, f'reviewed_{doc_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx')
        
        doc = Document(original_doc_path)
        
        doc.add_page_break()
        heading = doc.add_heading('Hawkeye Review Feedback Summary', 1)
        
        doc.add_paragraph(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        doc.add_paragraph(f'Total feedback items: {len(comments_data)}')
        doc.add_paragraph('')
        
        section_comments = defaultdict(list)
        for comment in comments_data:
            section_comments[comment['section']].append(comment)
        
        for section, comments in section_comments.items():
            section_heading = doc.add_heading(section, 2)
            
            for comment in comments:
                p = doc.add_paragraph(style='List Bullet')
                author = comment.get('author', 'AI Feedback')
                p.add_run(f"[{author}] {comment['type'].upper()} - {comment['risk_level']} Risk: ").bold = True
                p.add_run(comment['comment'])
        
        doc.save(output_path)
        return output_path
        
    except Exception as e:
        print(f"Error creating simple copy: {str(e)}")
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Create session
        session_id = str(uuid.uuid4())
        review_session = ReviewSession()
        review_session.session_id = session_id
        review_session.document_name = filename
        review_session.document_path = file_path
        
        try:
            # Open document
            doc = Document(file_path)
            review_session.document_object = doc
            
            # Extract sections
            sections, section_paragraphs, paragraph_indices = extract_document_sections_from_docx(doc)
            review_session.sections = sections
            review_session.section_paragraphs = section_paragraphs
            review_session.paragraph_indices = paragraph_indices
            
            document_sessions[session_id] = review_session
            session['session_id'] = session_id
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'sections': list(sections.keys()),
                'document_name': filename
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing document: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/analyze_section', methods=['POST'])
def analyze_section():
    data = request.json
    session_id = data.get('session_id')
    section_name = data.get('section_name')
    
    if not session_id or session_id not in document_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    review_session = document_sessions[session_id]
    
    if section_name not in review_session.sections:
        return jsonify({'error': 'Section not found'}), 400
    
    section_content = review_session.sections[section_name]
    
    # Check cache first
    cache_key = f"{section_name}_{hash(section_content)}"
    if cache_key in review_session.ai_feedback_cache:
        result = review_session.ai_feedback_cache[cache_key]
    else:
        result = analyze_section_with_ai(section_name, section_content)
        review_session.ai_feedback_cache[cache_key] = result
    
    return jsonify(result)

@app.route('/get_section', methods=['POST'])
def get_section():
    data = request.json
    session_id = data.get('session_id')
    section_name = data.get('section_name')
    
    if not session_id or session_id not in document_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    review_session = document_sessions[session_id]
    
    if section_name not in review_session.sections:
        return jsonify({'error': 'Section not found'}), 400
    
    return jsonify({
        'content': review_session.sections[section_name],
        'section_name': section_name
    })

@app.route('/accept_feedback', methods=['POST'])
def accept_feedback():
    data = request.json
    session_id = data.get('session_id')
    section_name = data.get('section_name')
    feedback_item = data.get('feedback_item')
    
    if not session_id or session_id not in document_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    review_session = document_sessions[session_id]
    
    if section_name not in review_session.accepted_feedback:
        review_session.accepted_feedback[section_name] = []
    
    review_session.accepted_feedback[section_name].append(feedback_item)
    
    # Prepare comment for Word document
    comment_text = f"[{feedback_item['type'].upper()} - {feedback_item.get('risk_level', 'Low')} Risk]\n"
    comment_text += f"{feedback_item['description']}\n"
    if feedback_item.get('suggestion'):
        comment_text += f"\nSuggestion: {feedback_item['suggestion']}\n"
    if feedback_item.get('hawkeye_refs'):
        refs = [f"#{r} {HAWKEYE_SECTIONS.get(r, '')}" for r in feedback_item['hawkeye_refs']]
        comment_text += f"\nHawkeye References: {', '.join(refs)}"
    
    # Store comment to be added to document
    if section_name in review_session.paragraph_indices and review_session.paragraph_indices[section_name]:
        review_session.document_comments.append({
            'section': section_name,
            'paragraph_index': review_session.paragraph_indices[section_name][0],
            'comment': comment_text,
            'type': feedback_item['type'],
            'risk_level': feedback_item.get('risk_level', 'Low'),
            'author': 'AI Feedback'
        })
    
    return jsonify({'success': True})

@app.route('/reject_feedback', methods=['POST'])
def reject_feedback():
    data = request.json
    session_id = data.get('session_id')
    section_name = data.get('section_name')
    feedback_item = data.get('feedback_item')
    
    if not session_id or session_id not in document_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    review_session = document_sessions[session_id]
    
    if section_name not in review_session.rejected_feedback:
        review_session.rejected_feedback[section_name] = []
        
    review_session.rejected_feedback[section_name].append(feedback_item)
    
    return jsonify({'success': True})

@app.route('/add_custom_feedback', methods=['POST'])
def add_custom_feedback():
    data = request.json
    session_id = data.get('session_id')
    section_name = data.get('section_name')
    feedback_type = data.get('type')
    category = data.get('category')
    description = data.get('description')
    
    if not session_id or session_id not in document_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    review_session = document_sessions[session_id]
    
    # Find Hawkeye reference number
    hawkeye_ref = 1
    for num, name in HAWKEYE_SECTIONS.items():
        if name == category:
            hawkeye_ref = num
            break
    
    feedback = {
        'id': str(uuid.uuid4()),
        'type': feedback_type,
        'category': category,
        'description': description,
        'suggestion': '',
        'hawkeye_refs': [hawkeye_ref],
        'risk_level': 'Medium' if feedback_type == 'critical' else 'Low',
        'timestamp': datetime.now().isoformat(),
        'user_created': True
    }
    
    if section_name not in review_session.user_feedback:
        review_session.user_feedback[section_name] = []
    
    review_session.user_feedback[section_name].append(feedback)
    
    # Also add as accepted feedback for comment
    if section_name not in review_session.accepted_feedback:
        review_session.accepted_feedback[section_name] = []
    review_session.accepted_feedback[section_name].append(feedback)
    
    # Prepare comment
    comment_text = f"[USER FEEDBACK - {feedback['type'].upper()}]\n"
    comment_text += f"{feedback['description']}\n"
    comment_text += f"\nHawkeye Reference: #{hawkeye_ref} {category}"
    
    if section_name in review_session.paragraph_indices and review_session.paragraph_indices[section_name]:
        review_session.document_comments.append({
            'section': section_name,
            'paragraph_index': review_session.paragraph_indices[section_name][0],
            'comment': comment_text,
            'type': feedback['type'],
            'risk_level': feedback['risk_level'],
            'user_created': True,
            'author': 'User Feedback'
        })
    
    return jsonify({'success': True, 'feedback': feedback})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id')
    query = data.get('query')
    context = data.get('context', {})
    
    if not session_id or session_id not in document_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    review_session = document_sessions[session_id]
    
    response = process_chat_query(query, context, session_id)
    
    # Store chat history
    review_session.chat_history.append({
        'role': 'user',
        'content': query,
        'timestamp': datetime.now().isoformat()
    })
    review_session.chat_history.append({
        'role': 'assistant',
        'content': response,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({'response': response})

@app.route('/complete_review', methods=['POST'])
def complete_review():
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id or session_id not in document_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    review_session = document_sessions[session_id]
    
    if not review_session.document_comments:
        return jsonify({'error': 'No feedback accepted. Please accept some feedback items first.'}), 400
    
    # Generate document
    if review_session.document_path and os.path.exists(review_session.document_path):
        output_path = create_reviewed_document_with_proper_comments(
            review_session.document_path,
            review_session.document_name,
            review_session.document_comments
        )
        
        if output_path and os.path.exists(output_path):
            return jsonify({
                'success': True,
                'output_path': os.path.basename(output_path),
                'comments_count': len(review_session.document_comments)
            })
    
    return jsonify({'error': 'Failed to generate reviewed document'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

@app.route('/get_stats', methods=['POST'])
def get_stats():
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id or session_id not in document_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    review_session = document_sessions[session_id]
    
    # Calculate statistics
    total_feedback = sum(len(items) for items in review_session.ai_feedback_cache.values())
    total_accepted = sum(len(items) for items in review_session.accepted_feedback.values())
    total_rejected = sum(len(items) for items in review_session.rejected_feedback.values())
    total_user = sum(len(items) for items in review_session.user_feedback.values())
    
    high_risk = 0
    medium_risk = 0
    
    for result in review_session.ai_feedback_cache.values():
        for item in result.get('feedback_items', []):
            if item.get('risk_level') == 'High':
                high_risk += 1
            elif item.get('risk_level') == 'Medium':
                medium_risk += 1
    
    return jsonify({
        'total_feedback': total_feedback,
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'accepted': total_accepted,
        'user_added': total_user
    })

# Load guidelines on startup
load_guidelines()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)