import os
import shutil
from PIL import Image

def crop_center(image: Image.Image, target_aspect: float) -> Image.Image:
    """Обрезает изображение так, чтобы его соотношение сторон соответствовало целевому."""
    width, height = image.size
    current_aspect = width / height
    
    if current_aspect > target_aspect:
        # Обрезаем по ширине
        new_width = int(height * target_aspect)
        left = (width - new_width) // 2
        right = left + new_width
        return image.crop((left, 0, right, height))
    else:
        # Обрезаем по высоте
        new_height = int(width / target_aspect)
        top = (height - new_height) // 2
        bottom = top + new_height
        return image.crop((0, top, width, bottom))

def determine_target_size(image: Image.Image):
    """Определяет целевое разрешение на основе соотношения сторон."""
    width, height = image.size
    aspect_ratio = width / height
    
    if 0.85 <= aspect_ratio <= 1.15:
        return (1024, 1024), 1.0  # Почти квадратные изображения
    else :
        return (832, 1216), 832 / 1216  # Вертикальные изображения
 

def resize_image(image: Image.Image, size) -> Image.Image:
    """Изменяет размер изображения до указанного разрешения."""
    return image.resize(size, Image.LANCZOS)

def clear_output_folder(folder):
    """Очищает папку перед сохранением новых файлов."""
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)

