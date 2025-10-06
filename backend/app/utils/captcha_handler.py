import io
import logging
import base64
from typing import Optional, Tuple
import re

import pytesseract
from PIL import Image
import numpy as np
import cv2
import requests

logger = logging.getLogger(__name__)

class CaptchaHandler:
    """Handles captcha detection, download, and solving"""
    
    def __init__(self):
        # Configure Tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        self.common_captcha_names = [
            'captcha', 'captchaCode', 'security_code', 
            'verification', 'secure_code', 'capt'
        ]
    
    def detect_captcha(self, html_content: str) -> Tuple[bool, Optional[dict]]:
        """Detect if page contains captcha and extract relevant info"""
        captcha_info = {
            'detected': False,
            'type': None,
            'image_url': None,
            'input_field': None
        }
        
        # Check for common captcha indicators in HTML
        captcha_patterns = [
            r'captcha',
            r'security.*code',
            r'verification.*image',
            r'prove.*human'
        ]
        
        if any(re.search(pattern, html_content, re.I) for pattern in captcha_patterns):
            captcha_info['detected'] = True
            
            # Try to find captcha image URL
            img_patterns = [
                r'<img[^>]*(?:id|class|alt)="[^"]*(?:captcha|security)[^"]*"[^>]*src="([^"]*)"',
                r'<img[^>]*src="([^"]*(?:captcha|security)[^"]*)"'
            ]
            
            for pattern in img_patterns:
                if match := re.search(pattern, html_content, re.I):
                    captcha_info['image_url'] = match.group(1)
                    break
            
            # Try to find input field
            input_patterns = [
                r'<input[^>]*(?:id|name)="[^"]*(?:captcha|security)[^"]*"[^>]*>',
                r'<input[^>]*name="([^"]*(?:captcha|code|verify)[^"]*)"[^>]*>'
            ]
            
            for pattern in input_patterns:
                if match := re.search(pattern, html_content, re.I):
                    captcha_info['input_field'] = match.group(1) if '(' in pattern else match.group(0)
                    break
        
        return captcha_info['detected'], captcha_info
    
    async def solve_captcha(self, image_url: str, session: requests.Session = None) -> Optional[str]:
        """Download and solve captcha"""
        try:
            # Download captcha image
            if session:
                response = session.get(image_url, stream=True)
            else:
                response = requests.get(image_url, stream=True)
            
            if response.status_code != 200:
                logger.error(f"Failed to download captcha: {response.status_code}")
                return None
            
            # Convert to image
            image = Image.open(io.BytesIO(response.content))
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # OCR with different preprocessing attempts
            for attempt in range(3):
                if text := pytesseract.image_to_string(processed_image):
                    # Clean up result
                    text = re.sub(r'[^a-zA-Z0-9]', '', text)
                    if text and 4 <= len(text) <= 8:  # Most captchas are 4-8 chars
                        logger.info(f"Solved captcha (attempt {attempt+1}): {text}")
                        return text
                
                # Try different preprocessing
                processed_image = self._alternative_preprocessing(image, attempt)
            
            logger.warning("Failed to solve captcha after all attempts")
            return None
            
        except Exception as e:
            logger.error(f"Captcha solving error: {str(e)}")
            return None
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Basic image preprocessing"""
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Basic thresholding
        _, thresh = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
        
        # Remove noise
        kernel = np.ones((2,2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return Image.fromarray(thresh)
    
    def _alternative_preprocessing(self, image: Image.Image, attempt: int) -> Image.Image:
        """Try different preprocessing techniques"""
        img_array = np.array(image)
        
        if attempt == 0:
            # Adaptive thresholding
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            processed = cv2.adaptiveThreshold(
                img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
        elif attempt == 1:
            # Edge enhancement
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            processed = cv2.Laplacian(img_array, cv2.CV_8U)
            processed = cv2.convertScaleAbs(processed)
            
        else:
            # Otsu's thresholding
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            blur = cv2.GaussianBlur(img_array, (5,5), 0)
            _, processed = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return Image.fromarray(processed)
