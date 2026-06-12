"""
Advanced image preprocessing for prescription OCR.
Applies multiple enhancement techniques for optimal text extraction.
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import os


def load_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        pil_img = Image.open(image_path).convert('RGB')
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return img


def resize_image(img, max_dim=2000):
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
    elif max(h, w) < 800:
        scale = 800 / max(h, w)
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
    return img


def deskew_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 10:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) > 15:
        return img
    (h, w) = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def apply_clahe(img):
    if len(img.shape) == 3:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        limg = cv2.merge((clahe.apply(l), a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    else:
        return cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(img)


def noise_reduction(img):
    if len(img.shape) == 3:
        return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    else:
        return cv2.fastNlMeansDenoising(img, None, 10, 7, 21)


def adaptive_threshold(gray):
    binary_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    binary_adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)
    return cv2.bitwise_and(binary_otsu, binary_adaptive)


def morphological_enhancement(binary_img):
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel)
    return cv2.dilate(cleaned, np.ones((1, 2), np.uint8), iterations=1)


def sharpen_image(img):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)


def enhance_contrast(img):
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img)
    enhanced = ImageEnhance.Sharpness(ImageEnhance.Contrast(pil_img).enhance(1.8)).enhance(2.0)
    return cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR) if len(img.shape) == 3 else np.array(enhanced)


def preprocess_for_ocr(image_path, output_dir=None):
    """Main preprocessing pipeline — returns dict of preprocessed image paths."""
    img = load_image(image_path)
    img = resize_image(img, max_dim=2500)
    img = deskew_image(img)

    results = {}

    # Version 1: Standard enhanced
    gray = cv2.cvtColor(noise_reduction(apply_clahe(img)), cv2.COLOR_BGR2GRAY)
    results['standard'] = adaptive_threshold(gray)

    # Version 2: High contrast binary
    gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    results['high_contrast'] = morphological_enhancement(
        cv2.threshold(gray2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])

    # Version 3: Sharpened
    gray3 = cv2.cvtColor(sharpen_image(img), cv2.COLOR_BGR2GRAY)
    results['sharpened'] = cv2.adaptiveThreshold(
        gray3, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 8)

    # Version 4: Color original
    results['color'] = img

    # Version 5: Contrast enhanced
    results['contrast'] = enhance_contrast(img)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(image_path))[0]
        saved_paths = {}
        for name, processed_img in results.items():
            path = os.path.join(output_dir, f"{base}_{name}.png")
            cv2.imwrite(path, processed_img)
            saved_paths[name] = path
        return saved_paths

    return results


def get_image_quality_score(image_path):
    """Estimate image quality — all values are plain Python types (JSON-safe)."""
    img = load_image(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    contrast = float(gray.std())

    # Use explicit Python bool() to avoid NumPy bool_ which is not JSON serializable
    is_blurry   = bool(blur_score < 100)
    is_too_dark  = bool(brightness < 50)
    is_too_bright = bool(brightness > 220)

    return {
        "blur_score":     round(blur_score, 2),
        "brightness":     round(brightness, 2),
        "contrast":       round(contrast, 2),
        "is_blurry":      is_blurry,
        "is_too_dark":    is_too_dark,
        "is_too_bright":  is_too_bright,
        "overall_quality": "good" if (not is_blurry and not is_too_dark and not is_too_bright) else "poor"
    }
