import random
from ursina import *

# ---------------------------------------------------------
# Vortex Wing - 3Dレールシューターベースコード
# 
# ※ 注意: 「Antigravity」はPythonのイースターエッグ（import antigravity）や
# 私たちAIアシスタントの名称であり、実際の3Dゲームエンジンではありません。
# そのため、このベースコードはPythonで最も簡単に3Dゲームを作成できる
# 「Ursina Engine」を使用して構築しています。
#
# 【実行前に必要なパッケージ】
# pip install ursina
# ---------------------------------------------------------

app = Ursina(title='Vortex Wing')

# --- プレイヤー機体クラス ---
class Player(Entity):
    def __init__(self):
        super().__init__(
            model='cube',           # 代用の基本図形（キューブ）
            color=color.azure,      # 機体の色
            scale=(1, 0.5, 1.5),    # 機体のサイズ
            position=(0, 0, 0),     # 初期位置
            collider='box'          # 当たり判定用コライダー
        )
        self.speed_z = 30           # 奥（Z軸）への前進速度
        self.speed_xy = 15          # 上下左右（X, Y軸）の移動速度
        self.hp = 100               # プレイヤーの耐久値
        self.score = 0              # スコア
        self.invincible = False     # 無敵状態フラグ
        self.invincible_timer = 0   # 無敵状態の残り時間
        
        # UI要素のセットアップ（画面にHPとスコアを表示）
        self.hp_text = Text(text=f'HP: {self.hp}', position=(-0.85, 0.45), scale=2, color=color.green)
        self.score_text = Text(text=f'SCORE: {self.score}', position=(0.6, 0.45), scale=2, color=color.white)
        self.game_over_text = Text(text='GAME OVER\nPress R to Restart', position=(0, 0), origin=(0,0), scale=3, color=color.red, enabled=False)
        
        # 画面中央の照準器（クロスヘア）
        self.crosshair = Text(text='+', position=(0, 0), origin=(0,0), scale=2, color=color.green)

    def update(self):
        if self.hp <= 0:
            return  # HPが0なら更新処理を停止（ゲームオーバー）

        # 1. Z軸（奥）への自動前進
        self.z += self.speed_z * time.dt
        
        # 2. X, Y軸（上下左右）の移動処理（WASDまたは矢印キー）
        dx = (held_keys['d'] - held_keys['a']) + (held_keys['right arrow'] - held_keys['left arrow'])
        dy = (held_keys['w'] - held_keys['s']) + (held_keys['up arrow'] - held_keys['down arrow'])
        
        self.x += dx * self.speed_xy * time.dt
        self.y += dy * self.speed_xy * time.dt
        
        # 画面外に出ないように移動範囲を制限（カメラが追従するため絶対座標で制限可能）
        self.x = clamp(self.x, -15, 15)
        self.y = clamp(self.y, -10, 10)
        
        # 3. 機体の傾き（ローリング）視覚効果
        # 左右移動時にZ軸回転（ロール）、上下移動時にX軸回転（ピッチ）
        target_roll = -dx * 30
        self.rotation_z = lerp(self.rotation_z, target_roll, time.dt * 10)
        target_pitch = -dy * 20
        self.rotation_x = lerp(self.rotation_x, target_pitch, time.dt * 10)
        
        # 4. 無敵時間の処理（バレルロール等の回避時）
        if self.invincible:
            self.invincible_timer -= time.dt
            # 無敵中は色を点滅（黄色）させる
            self.color = color.yellow if int(self.invincible_timer * 10) % 2 == 0 else color.azure
            if self.invincible_timer <= 0:
                self.invincible = False
                self.color = color.azure
        
    def input(self, key):
        if self.hp <= 0:
            if key == 'r':  # リスタート
                restart_game()
            return
            
        # 攻撃：スペースキーで前方にレーザーを発射
        if key == 'space':
            self.shoot()
            
        # 回避：QまたはEキーでバレルロール（横回転）
        if key == 'q' or key == 'e':
            self.barrel_roll(key)
            
    def shoot(self):
        # 機体の少し前方にレーザーを生成
        Laser(position=self.position + (0, 0, 2), direction=Vec3(0,0,1), is_player=True)
        
    def barrel_roll(self, key):
        if not self.invincible:
            self.invincible = True
            self.invincible_timer = 0.8  # 無敵時間
            # 回転アニメーション（Qで左回転、Eで右回転）
            roll_dir = 360 if key == 'q' else -360
            self.animate('rotation_z', self.rotation_z + roll_dir, duration=0.5, curve=curve.in_out_sine)
            
    def take_damage(self, amount):
        if not self.invincible and self.hp > 0:
            self.hp -= amount
            self.hp = max(0, self.hp)
            self.hp_text.text = f'HP: {self.hp}'
            
            # ダメージを受けた際のエフェクト（少し後ろに下がる）
            self.z -= 1.0
            
            if self.hp <= 0:
                self.game_over_text.enabled = True
                self.crosshair.enabled = False
                self.color = color.gray
                self.hp_text.color = color.red


# --- レーザー（弾）クラス ---
class Laser(Entity):
    def __init__(self, position, direction, is_player=True):
        super().__init__(
            model='cube',
            color=color.cyan if is_player else color.red,
            scale=(0.2, 0.2, 3) if is_player else (0.4, 0.4, 2),
            position=position,
            collider='box'
        )
        self.direction = direction
        self.speed = 100 if is_player else 60
        self.is_player = is_player
        self.life_time = 2.0  # 寿命（秒）
        
    def update(self):
        # 弾の移動
        self.position += self.direction * self.speed * time.dt
        self.life_time -= time.dt
        
        if self.life_time <= 0:
            destroy(self)
            return
            
        # 当たり判定処理
        hit_info = self.intersects()
        if hit_info.hit:
            if self.is_player:
                # プレイヤーの弾が敵に当たった場合
                if hasattr(hit_info.entity, 'is_enemy'):
                    hit_info.entity.take_damage(1)
                    destroy(self)
            else:
                # 敵の弾がプレイヤーに当たった場合
                if hit_info.entity == player:
                    player.take_damage(10)
                    destroy(self)


# --- 敵クラス ---
class Enemy(Entity):
    def __init__(self, position):
        super().__init__(
            model='diamond',        # 敵の代用モデル
            color=color.orange,
            scale=(2, 2, 2),
            position=position,
            collider='box'
        )
        self.is_enemy = True
        self.hp = 2
        self.shoot_timer = random.uniform(1, 3)  # 初回射撃までのランダムな時間
        
    def update(self):
        if player.hp <= 0:
            return
            
        # プレイヤーに向かって少し移動する（Z軸マイナス方向）
        self.z -= 15 * time.dt
        
        # 画面の奥過ぎる、またはプレイヤーより手前に来たら消去
        if self.z < player.z - 20:
            destroy(self)
            return
        
        # プレイヤーに向かって弾を撃つ
        self.shoot_timer -= time.dt
        if self.shoot_timer <= 0:
            self.shoot_timer = random.uniform(1.5, 3.5)
            # プレイヤーの方向を計算
            direction = (player.position - self.position).normalized()
            Laser(position=self.position + (0, 0, -2), direction=direction, is_player=False)
            
        # プレイヤーとの直接衝突判定
        if self.intersects(player).hit:
            player.take_damage(20)
            self.take_damage(99)  # 衝突で敵は消滅

    def take_damage(self, amount):
        self.hp -= amount
        # ダメージエフェクト（白く光る）
        self.color = color.white
        invoke(setattr, self, 'color', color.orange, delay=0.1)
        
        if self.hp <= 0:
            if player.hp > 0:
                player.score += 100
                player.score_text.text = f'SCORE: {player.score}'
            destroy(self)


# --- 障害物クラス ---
class Obstacle(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.dark_gray,
            scale=(random.uniform(2, 6), random.uniform(2, 6), random.uniform(2, 6)),
            position=position,
            collider='box'
        )
        # 障害物は回転させながら配置
        self.rotation = (random.randint(0,360), random.randint(0,360), random.randint(0,360))
        
    def update(self):
        # プレイヤーを通り過ぎたら消去
        if self.z < player.z - 20:
            destroy(self)
            return
            
        # プレイヤーとの衝突判定
        if self.intersects(player).hit:
            player.take_damage(15)


# --- ゲームシステム管理 ---

def spawn_objects():
    if player.hp <= 0:
        return
        
    # プレイヤーのZ座標から一定距離離れた奥（Z軸）に生成
    spawn_z = player.z + 200
    spawn_x = random.uniform(-20, 20)
    spawn_y = random.uniform(-15, 15)
    
    # 敵と障害物をランダムに生成
    if random.random() > 0.4:
        Enemy(position=(spawn_x, spawn_y, spawn_z))
    else:
        Obstacle(position=(spawn_x, spawn_y, spawn_z))

class GameManager(Entity):
    def __init__(self):
        super().__init__()
        self.spawn_timer = 0
        
    def update(self):
        # グリッド（背景）をプレイヤーに追従させて無限に続くように見せる
        grid.z = player.z - (player.z % 10)
        
        # オブジェクトの定期生成
        if player.hp > 0:
            self.spawn_timer -= time.dt
            if self.spawn_timer <= 0:
                spawn_objects()
                # 進行するにつれて生成間隔を短くする（最低0.3秒）
                interval = max(0.3, 1.0 - (player.score / 5000))
                self.spawn_timer = random.uniform(interval, interval * 1.5)

def restart_game():
    global player
    # 既存の敵、障害物、弾を削除
    for e in scene.entities:
        if isinstance(e, (Enemy, Obstacle, Laser)):
            destroy(e)
            
    # プレイヤーの状態をリセット
    player.position = (0, 0, 0)
    player.hp = 100
    player.score = 0
    player.hp_text.text = f'HP: {player.hp}'
    player.score_text.text = f'SCORE: {player.score}'
    player.hp_text.color = color.green
    player.color = color.azure
    player.game_over_text.enabled = False
    player.crosshair.enabled = True

# --- シーンの初期化 ---

# プレイヤーのインスタンス化
player = Player()

# ゲームマネージャー（スポナー）
game_manager = GameManager()

# 背景のグリッド（スピード感を演出）
grid = Entity(model=Grid(100, 100), scale=1000, color=color.rgba(0, 0, 128, 128), rotation_x=90, position=(0, -20, 0))
# 上部のグリッド（トンネル感）
grid_top = Entity(model=Grid(100, 100), scale=1000, color=color.rgba(128, 0, 128, 76), rotation_x=90, position=(0, 20, 0))

def update():
    # 上部のグリッドも追従
    grid_top.z = player.z - (player.z % 10)

# カメラの設定（プレイヤーの後方斜め上からのTPS視点）
camera.parent = player
camera.position = (0, 4, -15)
camera.rotation_x = 10
# カメラのFOVを少し広げてスピード感を出す
camera.fov = 100

# ライトの設定
DirectionalLight(y=2, z=3, shadows=True, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(100, 100, 100, 1))

# 背景色
window.color = color.black

# ゲーム開始
app.run()
