from django import template

register = template.Library()

@register.filter
def split_lines(value, separator="<br />"):
    """Разделяет строку по разделителю и возвращает список"""
    if not value:
        return []
    return value.split(separator)

@register.filter
def extract_attachments(value):
    """Извлекает информацию о вложениях из описания задачи"""
    if not value or "Вложения:" not in value:
        return []
    
    attachments = []
    
    # Разделяем по переносам строк
    lines = value.split("\n")
    
    # Ищем все строки с эмодзи вложений
    for line in lines:
        line = line.strip()
        if "📸" in line or "📎" in line:
            # Извлекаем имя файла (убираем эмодзи и пробелы)
            filename = line.replace("📸", "").replace("📎", "").strip()
            
            if filename:
                attachments.append({
                    'type': 'photo' if "📸" in line else 'document',
                    'filename': filename
                })
    
    return attachments
