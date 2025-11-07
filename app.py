from flask import Flask, request, jsonify, redirect, session, send_from_directory
from deepface import DeepFace
import os, shutil, base64, cv2, numpy as np
from datetime import datetime


app = Flask(__name__, static_folder='static')
app.secret_key = "super_secret_key" 

IMAGES_DIR = 'images'
os.makedirs(IMAGES_DIR, exist_ok=True)


print("🔄 Facenet512 modeli yuklanmoqda...")
DeepFace.build_model("Facenet512")
print("✅ Model tayyor!")

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('static', 'admin.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    return send_from_directory('static', 'dashboard.html')


@app.route('/auth', methods=['POST'])
def auth():
    print("📸 /auth endpoint ishladi")

    data = request.get_json()
    print("🔹 JSON ma'lumot:", data)

    img_b64 = data.get('image')
    if not img_b64:
        return jsonify({'success': False, 'message': 'Rasm yuborilmadi'})

    # 🎞️ Rasmni decode qilish
    if ',' in img_b64:
        img_b64 = img_b64.split(',')[1]

    try:
        probe = cv2.imdecode(np.frombuffer(base64.b64decode(img_b64), np.uint8), cv2.IMREAD_COLOR)
        print("✅ Kamera rasmi olindi. Endi yuzni solishtiryapmiz...")
    except Exception as e:
        print("❌ Decode xato:", e)
        return jsonify({'success': False, 'message': 'Rasmni o‘qishda xatolik'})

    for username in os.listdir(IMAGES_DIR):
        user_dir = os.path.join(IMAGES_DIR, username)
        if not os.path.isdir(user_dir):
            continue

        for file in os.listdir(user_dir):
            saved_path = os.path.join(user_dir, file)
            print(f"🔎 {username} bilan solishtirilmoqda: {file}")

            try:
                res = DeepFace.verify(
                    probe,
                    saved_path,
                    model_name="Facenet512",
                    enforce_detection=False
                )
                print("📊 Natija:", res)

                if res.get('verified'):
                    session['username'] = username

                    login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    confidence = round((1 - res.get('distance', 0)) * 100, 2)

                    role = "admin" if username.lower() == "admin" else "user"
                    redirect_url = "/admin/dashboard" if role == "admin" else "/dashboard"

                    print(f"✅ {username} ({role}) tizimga kirdi | O‘xshashlik: {confidence}%")

                    return jsonify({
                        'success': True,
                        'message': f'Xush kelibsiz, {username}!',
                        'role': role,
                        'login_time': login_time,
                        'confidence': confidence,
                        'redirect': redirect_url
                    })

            except Exception as e:
                print("⚠️ Solishtirishda xato:", e)
                continue

    print("❌ Hech kim mos kelmadi.")
    return jsonify({
        'success': False,
        'message': 'Yuz tanilmadi yoki foydalanuvchi mavjud emas.'
    })

# 🧾 Admin orqali rasm yuklash (foydalanuvchini bazaga qo‘shish)
@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    data = request.get_json()
    username = data['username']
    img_b64 = data['image']

    user_dir = os.path.join(IMAGES_DIR, username)
    os.makedirs(user_dir, exist_ok=True)

    if ',' in img_b64:
        img_b64 = img_b64.split(',')[1]

    img = cv2.imdecode(np.frombuffer(base64.b64decode(img_b64), np.uint8), cv2.IMREAD_COLOR)
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    cv2.imwrite(os.path.join(user_dir, filename), img)

    print(f"💾 {username} uchun rasm saqlandi: {filename}")
    return jsonify({'success': True, 'message': f'{username} uchun rasm bazaga saqlandi.'})



@app.route('/admin/users')
def admin_users():
    users = []
    for username in os.listdir(IMAGES_DIR):
        path = os.path.join(IMAGES_DIR, username)
        if not os.path.isdir(path): 
            continue

        images = len(os.listdir(path))
        created = datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d %H:%M:%S")
        role = "admin" if username.lower() == "admin" else "user"

        users.append({
            "username": username,
            "role": role,
            "created": created,
            "images": images
        })

    return jsonify(users)


@app.route('/admin/delete/<username>', methods=['DELETE'])
def delete_user(username):
    user_dir = os.path.join(IMAGES_DIR, username)
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
        return jsonify({'success': True, 'message': f"{username} o‘chirildi."})
    else:
        return jsonify({'success': False, 'message': 'Foydalanuvchi topilmadi.'})


@app.route('/logout')
def logout():
    session.clear()  # sessiyani tozalaydi
    return redirect('/') 

if __name__ == '__main__':
    app.run(debug=True)


