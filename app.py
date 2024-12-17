from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///water_intake.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 資料庫模型
class WaterIntake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)  # 體重（kg）
    daily_water_requirement = db.Column(db.Float, nullable=False)  # 每日所需飲水量（cc）
    current_water_intake = db.Column(db.Float, default=0)  # 目前的飲水量（cc）
    last_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, weight):
        self.weight = weight
        self.daily_water_requirement = self.calculate_daily_intake(weight)
        self.current_water_intake = 0

    def calculate_daily_intake(self, weight):
        # 計算每日所需飲水量（cc），假設每公斤體重大約需要 30cc 水
        return weight * 30
    
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)  # 使用者體重
    daily_required = db.Column(db.Integer, nullable=False)  # 每日所需飲水量
    current_intake = db.Column(db.Integer, nullable=False, default=0)  # 目前飲水量
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 最後更新時間
    reminder_interval = db.Column(db.Integer, default=40)  # 提醒時間間隔，預設40分鐘
    reminder_active = db.Column(db.Boolean, default=True)  # 提醒開關，預設開啟

    def __repr__(self):
        return f"<UserProfile {self.id}>"

# 初始化資料庫
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # 獲取目前的飲水量與每日所需飲水量
    water_intake = WaterIntake.query.first()
    if water_intake is None:
        # 如果資料庫為空，創建一個新的條目
        water_intake = WaterIntake(weight=70)  # 預設體重為 70kg
        db.session.add(water_intake)
        db.session.commit()

    return render_template('index.html', 
                           daily_water_requirement=water_intake.daily_water_requirement, 
                           current_water_intake=water_intake.current_water_intake)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    water_intake = WaterIntake.query.first()
    if request.method == 'POST':
        new_weight = request.form['weight']
        if new_weight and new_weight.isdigit():
            water_intake.weight = float(new_weight)
            water_intake.daily_water_requirement = water_intake.calculate_daily_intake(float(new_weight))
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('profile.html', weight=water_intake.weight)

@app.route('/api/add', methods=['POST'])
def add_water():
    data = request.json
    water_intake = WaterIntake.query.first()
    if water_intake:
        water_intake.current_water_intake += data.get('amount', 0)
        db.session.commit()
        return jsonify({"message": "Water added", "current_water_intake": water_intake.current_water_intake})
    return jsonify({"message": "Water intake not found"}), 404

@app.route('/api/total', methods=['GET'])
def total_water():
    water_intake = WaterIntake.query.first()
    if water_intake:
        return jsonify({
            "daily_water_requirement": water_intake.daily_water_requirement,
            "current_water_intake": water_intake.current_water_intake
        })
    return jsonify({"message": "Water intake not found"}), 404

@app.route('/set_timer', methods=['GET', 'POST'])
def set_timer():
    user_profile = UserProfile.query.first()
    if request.method == 'POST':
        try:
            # 更新提醒間隔時間和開關狀態
            reminder_interval = int(request.form['reminder_interval'])
            reminder_active = 'reminder_active' in request.form  # 檢查是否勾選 "開啟提醒"
            user_profile.reminder_interval = reminder_interval
            user_profile.reminder_active = reminder_active
            db.session.commit()
            return redirect(url_for('index'))
        except ValueError:
            pass  # 錯誤處理，保持原值
    return render_template('set_timer.html', user_profile=user_profile)
from datetime import datetime

@app.route('/api/reset', methods=['POST'])
def reset_water_intake():
    water_intake = WaterIntake.query.first()
    if water_intake:
        water_intake.current_water_intake = 0  # 重置飲水量
        water_intake.last_reset = datetime.utcnow()  # 更新最後重置時間
        db.session.commit()
        return jsonify({"message": "Water intake has been reset"})
    return jsonify({"message": "Water intake not found"}), 404

if __name__ == '__main__':
    app.run()
