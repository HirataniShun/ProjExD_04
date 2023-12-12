import math
import os
import random
import sys
import time
from typing import Any
import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"  # 状態の変数
        self.hyper_life = 0  # 発動時間の変数
        self.hyper_key_pressed_last_frame = False

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface, score: Score):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        self.speed = 10  # 追加機能1
        if key_lst[pg.K_LSHIFT]:  #左シフト押下時スピードアップ
            self.speed = 20
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)
        hyper_key_pressed_current_frame = key_lst[pg.K_RSHIFT]  # 現在のフレームで右Shiftキーが押されているかどうか
        if (hyper_key_pressed_current_frame and not self.hyper_key_pressed_last_frame
        and score.value >= 100):  # 右shiftキーが押されたとき、かつ、スコア>100の時
            self.state = "hyper"  # ステータスを無敵に変更
            self.hyper_life += 500  # 無敵時間を500フレーム追加
            score.value -= 100
        self.hyper_key_pressed_last_frame = hyper_key_pressed_current_frame  # 状態を更新
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)  # 無敵状態の画像に変更
            self.hyper_life -= 1
            if self.hyper_life <= 0:  # 無敵時間が0になった時
                self.state = "normal"  # ステータスをノーマルに変更
        

class Shield(pg.sprite.Sprite):
    """
    防御壁のクラス
    """
    def __init__(self, bird: Bird, life):
        super().__init__()
        kx, ky = bird.dire
        angle = math.degrees(math.atan2(-ky, kx))
        self.image = pg.Surface((20, bird.rect.height*2))
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, 20, bird.rect.height*2))
        self.image = pg.transform.rotozoom(self.image, angle, 1)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*ky
        self.rect.centerx = bird.rect.centerx+bird.rect.width*kx
        self.life = life

    def update(self, bird: Bird):
        self.life -= 1                
        kx, ky = bird.dire
        angle = math.degrees(math.atan2(-ky, kx))
        self.image = pg.Surface((20, bird.rect.height*2))
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, 20, bird.rect.height*2))
        self.image = pg.transform.rotozoom(self.image, angle, 1)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*ky
        self.rect.centerx = bird.rect.centerx+bird.rect.width*kx
        if self.life < 0:
            self.kill()
            


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0:int =0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        angle += angle0  #追加機能6
        self.image = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class NeoBeam:  #追加機能6
    def __init__(self, bird: Bird, num:int):
        self.bird = bird
        self.num = num

    def gen_beams(self):
        beams = list()  #beamを格納するリスト
        for r in range(-50, +51, 100//(self.num-1)):  #ビームをnum個生成
            beams.append(Beam(self.bird, r))
        return beams  #beamのリストを返す


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"{MAIN_DIR}/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"{MAIN_DIR}/fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


#追加機能3
class EMP():
    """
    電磁パルスを生成する
    """
    def __init__(self,emys,bombs,screen,score):
        self.image = pg.Surface((WIDTH,HEIGHT))
        pg.draw.rect(self.image,[255,217,0],(0,0,WIDTH,HEIGHT))
        self.image.set_alpha(50)
        score.value -= 20
        for i in emys:
            i.interval = "inf"
            i.image = pg.transform.laplacian(i.image)
            i.image.set_colorkey((0,0,0))
        for bomb in bombs:
            bomb.speed *= 0.5
            bomb.state = "inactive"    
        screen.blit(self.image,self.image.get_rect())
        pg.display.update()
        time.sleep(0.05)
    
    
class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self, ini_score=0):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = ini_score
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"{MAIN_DIR}/fig/pg_bg.jpg")
    score = Score()
    neobeams = list()
    neobeam_flag = False

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    
    shields = pg.sprite.Group()
    hyper_font = pg.font.Font(None, 50)  # 無敵時間用のフォント
    hyper_color = (0, 0, 255)  # 無敵時間の表示色

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:  #追加機能6
                neobeam_flag = True
            if event.type == pg.KEYUP and event.key == pg.K_LSHIFT:  #追加機能6
                neobeam_flag = False
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if not neobeam_flag:  #追加機能6
                    beams.add(Beam(bird))  #通常のビーム
                else:
                    neobeams = NeoBeam(bird, 5).gen_beams()  #n個のビームを生成
                    for i in neobeams:  #生成したビームをbeamsに追加
                        beams.add(i)
            if (event.type == pg.KEYDOWN and event.key == pg.K_CAPSLOCK
                and score.value >= 50 and len(shields) <= 0):
                shields.add(Shield(bird, 400))
            if event.type == pg.KEYDOWN and event.key == pg.K_e and score.value >= 20:
                EMP(emys,bombs,screen,score)
        screen.blit(bg_img, [0, 0])

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.interval != "inf":
                if emy.state == "stop" and tmr%emy.interval == 0:
                    # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                    bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
        
        if bird.state == "hyper" and collided_bombs:  # 無敵状態の時
            for bomb in collided_bombs:
                exps.add(Explosion(bomb, 50))  # 爆発エフェクトを追加
                bomb.kill()  # 衝突した爆弾を削除
                score.value += 1  # スコアを1アップ
                
        elif collided_bombs:  # 無敵ではない時
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        if bird.state == "hyper":  # 無敵時間の時
            hyper_text = hyper_font.render(f"Hyper Time: {bird.hyper_life // 50}", True, hyper_color)
            hyper_pos = (WIDTH - hyper_text.get_width() - 10, HEIGHT - hyper_text.get_height() - 10)
            screen.blit(hyper_text, hyper_pos)  # 無敵の残り時間を表示

        bird.update(key_lst, screen, score)
        shields.update(bird)
        shields.draw(screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
