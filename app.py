from flask import Flask, request, render_template, session
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
import os
from io import BytesIO
import base64
from captcha.image import ImageCaptcha
import random
import string

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Секретный ключ для работы сессий
app.secret_key = 'your_secret_key_here'  # Замените на ваш собственный секретный ключ

# Директория для сохранения загруженных изображений
UPLOAD_FOLDER = 'static/uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Проверка капчи
        user_captcha = request.form.get('captcha')
        session_captcha = session.get('session_captcha')
        if user_captcha != session_captcha:
            # Генерация новой капчи
            captcha_text, captcha_image = generate_captcha()
            session['session_captcha'] = captcha_text
            return render_template('index.html',
                                   error="Введена неверная капча. Пробуйте снова.",
                                   captcha_image=captcha_image,
                                   session_captcha=captcha_text)

        # Получение файла изображения и коэффициента интенсивности
        image_file = request.files.get('image')
        intensity_factor = request.form.get('intensity')

        if not image_file or not intensity_factor:
            return render_template('index.html',
                                   error="Пожалуйста, загрузите изображение и укажите коэффициент интенсивности.")

        intensity_factor = float(intensity_factor)

        if image_file:
            # Сохранение изображения
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
            image_file.save(image_path)

            # Открытие изображения и изменение его интенсивности
            image = Image.open(image_path)
            enhancer = ImageEnhance.Color(image)
            enhanced_image = enhancer.enhance(intensity_factor)

            # Сохранение нового изображения
            enhanced_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced_' + image_file.filename)
            enhanced_image.save(enhanced_image_path)

            # Генерация графиков
            original_histogram = generate_histogram(image)
            enhanced_histogram = generate_histogram(enhanced_image)

            return render_template('index.html',
                                   original_image=image_file.filename,
                                   enhanced_image='enhanced_' + image_file.filename,
                                   original_histogram=original_histogram,
                                   enhanced_histogram=enhanced_histogram)
    else:
        # Генерация капчи
        captcha_text, captcha_image = generate_captcha()
        session['session_captcha'] = captcha_text
        return render_template('index.html', captcha_image=captcha_image, session_captcha=captcha_text)


# Функция генерации гистограммы изображения
def generate_histogram(image):
    plt.figure(figsize=(8, 4))
    for color, color_name in zip(image.convert('RGB').getbands(), ['red', 'green', 'blue']):
        plt.hist(image.getchannel(color).getdata(), bins=256, color=color_name, alpha=0.7)
    plt.title('Color Distribution')
    plt.xlabel('Pixel value')
    plt.ylabel('Frequency')

    # Сохранение гистограммы в памяти как изображение
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    # Конвертация изображения в base64 для отображения в браузере
    histogram_image = base64.b64encode(buf.getvalue()).decode('utf-8')
    return histogram_image


# Функция генерации капчи
def generate_captcha():
    captcha = ImageCaptcha()
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    image = captcha.generate_image(captcha_text)

    # Сохранение капчи в памяти как изображение
    buf = BytesIO()
    image.save(buf, format='png')
    buf.seek(0)

    # Конвертация изображения в base64 для отображения в браузере
    captcha_image = base64.b64encode(buf.getvalue()).decode('utf-8')
    return captcha_text, captcha_image


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Получаем порт из переменной окружения или используем 5000 по умолчанию
    app.run(host="0.0.0.0", port=port)
